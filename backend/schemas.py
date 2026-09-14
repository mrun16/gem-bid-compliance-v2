from typing import Optional
from pydantic import BaseModel


class RequirementResult(BaseModel):
    requirement: str
    status: str  # PASS / FAIL / INCONSISTENT / UNVERIFIABLE
    evidence: str
    category: Optional[str] = None      # threaded back in from the tender checklist
    category_help: Optional[str] = None  # plain-English tooltip text for the frontend


class VerificationResponse(BaseModel):
    blocked: bool
    block_reason: Optional[str] = None
    alignment_warning: Optional[str] = None

    bidder_pan: Optional[str] = None
    bidder_name: Optional[str] = None
    injection_hits: list[str] = []

    compliance_score: Optional[int] = None
    risk_level: Optional[str] = None
    flags: list[str] = []
    recommendation: Optional[str] = None
    requirement_results: list[RequirementResult] = []
    rule_results: list[dict] = []
    rule_engine_resolved_count: int = 0
    checklist_total_count: int = 0

    error: Optional[str] = None
    raw_response: Optional[str] = None


class AuditEntryCreate(BaseModel):
    bidder_pan: str
    bidder_name: str
    compliance_score: int
    risk_level: str
    flags: list[str] = []
    ai_recommendation: str = ""
    officer_decision: str
    officer_notes: str = ""
    requirement_results: list[dict] = []
    rule_results: list[dict] = []


class AuditEntry(AuditEntryCreate):
    id: int
    timestamp: str


class ReportRequest(BaseModel):
    bidder_pan: str
    bidder_name: str
    compliance_score: int
    risk_level: str
    flags: list[str] = []
    recommendation: str = ""
    requirement_results: list[dict] = []
    rule_results: list[dict] = []
    officer_decision: str = "Not yet decided"
    officer_notes: str = ""
