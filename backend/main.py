"""
FastAPI backend for the GeM Bid Compliance Verification Platform (V2).

Run with:  uvicorn main:app --reload --port 8000
Docs at:   http://localhost:8000/docs   (FastAPI generates this automatically)
"""
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

import database
import verification_service as vs
from config import CORS_ORIGINS, OFFICER_ACCESS_CODE
from schemas import VerificationResponse, AuditEntryCreate, AuditEntry, ReportRequest

app = FastAPI(
    title="GeM Bid Compliance Verification API",
    description="Backend for SIH26100 — decision-support only, never a final approval authority.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    database.init_db()


def require_officer_access(x_officer_code: Optional[str] = Header(default=None)):
    """Simple shared-secret gate for audit-trail endpoints, same idea as the
    V1 Streamlit password box. Swap for real government SSO in production."""
    if x_officer_code != OFFICER_ACCESS_CODE:
        raise HTTPException(status_code=401, detail="Invalid or missing officer access code.")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/verify", response_model=VerificationResponse)
async def verify(
    tender_file: UploadFile = File(...),
    vendor_file: UploadFile = File(...),
    bidder_pan: str = Form(...),
):
    if not bidder_pan.strip():
        raise HTTPException(status_code=400, detail="Bidder PAN is required.")

    tender_bytes = await tender_file.read()
    vendor_bytes = await vendor_file.read()

    portal_db = database.load_portal_database()
    portal_record = portal_db.get(bidder_pan.strip().upper())

    try:
        result = vs.run_full_pipeline(tender_bytes, vendor_bytes, bidder_pan, portal_record)
    except RuntimeError as e:
        # e.g. missing GEMINI_API_KEY
        raise HTTPException(status_code=500, detail=str(e))

    result.setdefault("blocked", False)
    return result


@app.post("/audit", response_model=AuditEntry)
def create_audit_entry(entry: AuditEntryCreate, _=None):
    saved = database.insert_audit_entry(
        bidder_pan=entry.bidder_pan,
        bidder_name=entry.bidder_name,
        compliance_score=entry.compliance_score,
        risk_level=entry.risk_level,
        flags=entry.flags,
        ai_recommendation=entry.ai_recommendation,
        officer_decision=entry.officer_decision,
        officer_notes=entry.officer_notes,
        requirement_results=entry.requirement_results,
        rule_results=entry.rule_results,
    )
    return saved


@app.get("/audit", response_model=list[AuditEntry])
def get_audit_trail(_=None, x_officer_code: Optional[str] = Header(default=None)):
    require_officer_access(x_officer_code)
    return database.list_audit_entries()


@app.get("/portal-database")
def get_portal_database(x_officer_code: Optional[str] = Header(default=None)):
    require_officer_access(x_officer_code)
    return database.load_portal_database()


@app.post("/report/preview")
def generate_report_preview(req: ReportRequest):
    """Generate a PDF report before saving to the audit trail (e.g. the officer
    wants to download and review before committing a decision)."""
    pdf_bytes = vs.generate_compliance_pdf(
        bidder_name=req.bidder_name,
        bidder_pan=req.bidder_pan,
        score=req.compliance_score,
        risk=req.risk_level,
        flags=req.flags,
        recommendation=req.recommendation,
        requirement_results=req.requirement_results,
        rule_results=req.rule_results,
        officer_decision=req.officer_decision,
        officer_notes=req.officer_notes,
    )
    return Response(content=pdf_bytes, media_type="application/pdf")


@app.get("/audit/{entry_id}/report")
def generate_report_from_audit(entry_id: int, x_officer_code: Optional[str] = Header(default=None)):
    """Regenerate the PDF for an already-saved audit entry."""
    require_officer_access(x_officer_code)
    entry = database.get_audit_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Audit entry not found.")
    pdf_bytes = vs.generate_compliance_pdf(
        bidder_name=entry["bidder_name"],
        bidder_pan=entry["bidder_pan"],
        score=entry["compliance_score"],
        risk=entry["risk_level"],
        flags=entry["flags"],
        recommendation=entry["ai_recommendation"],
        requirement_results=entry["requirement_results"],
        rule_results=entry["rule_results"],
        officer_decision=entry["officer_decision"],
        officer_notes=entry["officer_notes"],
    )
    return Response(content=pdf_bytes, media_type="application/pdf")
