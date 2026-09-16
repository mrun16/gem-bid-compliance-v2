"""
FastAPI backend for the GeM Bid Compliance Verification Platform (V2).

Run with:
    uvicorn main:app --reload --port 8000

Docs:
    http://localhost:8000/docs
"""

from typing import Optional

from fastapi import (
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

import database
import verification_service as vs
from config import CORS_ORIGINS, OFFICER_ACCESS_CODE
from schemas import (
    VerificationResponse,
    AuditEntryCreate,
    AuditEntry,
    ReportRequest,
)


app = FastAPI(
    title="GeM Bid Compliance Verification API",
    description=(
        "Backend for SIH26100 — decision-support only, "
        "never a final approval authority."
    ),
    version="2.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# STARTUP
# ---------------------------------------------------------

@app.on_event("startup")
def on_startup():
    database.init_db()


# ---------------------------------------------------------
# OFFICER ACCESS
# ---------------------------------------------------------

def require_officer_access(
    x_officer_code: Optional[str] = Header(default=None),
):
    """
    Simple shared-secret gate for audit-trail endpoints.

    This is the V2 prototype version of the officer password gate.
    In production, this could be replaced with government SSO.
    """

    if x_officer_code != OFFICER_ACCESS_CODE:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing officer access code.",
        )


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------
# BID VERIFICATION
# ---------------------------------------------------------

@app.post(
    "/verify",
    response_model=VerificationResponse,
)
async def verify(
    tender_file: UploadFile = File(...),
    vendor_file: UploadFile = File(...),
    bidder_pan: str = Form(...),
):
    # Check PAN
    if not bidder_pan.strip():
        raise HTTPException(
            status_code=400,
            detail="Bidder PAN is required.",
        )

    # Read uploaded files
    tender_bytes = await tender_file.read()
    vendor_bytes = await vendor_file.read()

    # Load mock portal database
    portal_db = database.load_portal_database()

    portal_record = portal_db.get(
        bidder_pan.strip().upper()
    )

    # Run complete verification pipeline
    try:
        result = vs.run_full_pipeline(
            tender_bytes,
            vendor_bytes,
            bidder_pan,
            portal_record,
        )

    except RuntimeError as e:
        # Example:
        # Missing GEMINI_API_KEY
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    # Make sure blocked always exists
    result.setdefault("blocked", False)

    return result


# ---------------------------------------------------------
# AUDIT TRAIL - SAVE
# ---------------------------------------------------------

@app.post(
    "/audit",
    response_model=AuditEntry,
)
def create_audit_entry(
    entry: AuditEntryCreate,
):
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


# ---------------------------------------------------------
# AUDIT TRAIL - VIEW
# ---------------------------------------------------------

@app.get(
    "/audit",
    response_model=list[AuditEntry],
)
def get_audit_trail(
    x_officer_code: Optional[str] = Header(default=None),
):
    require_officer_access(x_officer_code)

    return database.list_audit_entries()


# ---------------------------------------------------------
# PORTAL DATABASE
# ---------------------------------------------------------

@app.get("/portal-database")
def get_portal_database(
    x_officer_code: Optional[str] = Header(default=None),
):
    require_officer_access(x_officer_code)

    return database.load_portal_database()


# ---------------------------------------------------------
# REPORT PREVIEW
# ---------------------------------------------------------

@app.post("/report/preview")
def generate_report_preview(
    req: ReportRequest,
):
    """
    Generate a PDF report before saving it to the audit trail.

    The officer can review the report before committing
    the final decision.
    """

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

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
    )


# ---------------------------------------------------------
# REPORT FROM SAVED AUDIT ENTRY
# ---------------------------------------------------------

@app.get("/audit/{entry_id}/report")
def generate_report_from_audit(
    entry_id: int,
    x_officer_code: Optional[str] = Header(default=None),
):
    """
    Regenerate the PDF report for an already-saved
    audit entry.
    """

    # Check officer access first
    require_officer_access(x_officer_code)

    # Find audit entry
    entry = database.get_audit_entry(entry_id)

    if not entry:
        raise HTTPException(
            status_code=404,
            detail="Audit entry not found.",
        )

    # Generate PDF
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

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
    )