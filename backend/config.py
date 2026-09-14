"""
Central config for the FastAPI backend. Reads from environment variables,
optionally loaded from a local .env file (see .env.example).

Nothing here costs money by itself — the only line item in this whole stack
is Gemini API usage past Google's free tier (aistudio.google.com).
"""
import os
from dotenv import load_dotenv

load_dotenv()  # no-op if there's no .env file present

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "audit_trail.db"))
MOCK_PORTAL_PATH = os.environ.get(
    "MOCK_PORTAL_PATH", os.path.join(os.path.dirname(__file__), "mock_portal_data.json")
)

# Simple shared-secret gate for the audit trail endpoints — same idea as the
# V1 Streamlit password box. Swap for real government SSO in production.
OFFICER_ACCESS_CODE = os.environ.get("OFFICER_ACCESS_CODE", "officer2026")

# Comma-separated list of origins allowed to call this API (the Streamlit
# frontend's URL). Defaults cover local dev on the default Streamlit port.
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501"
).split(",")
