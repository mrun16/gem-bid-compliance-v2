# GeM Bid Compliance Verification Platform — V2

**SIH26100 MVP.** Same working pipeline as V1, restructured behind a real API layer with a real database.

## What changed from V1

| | V1 | V2 |
|---|---|---|
| Frontend | Streamlit (does everything) | Streamlit (thin client only) |
| Backend logic | Inline in `app.py` | FastAPI service, `POST /verify` etc. |
| Storage | Flat JSON file (`audit_trail.json`) | SQLite (`audit_trail.db`) — a real relational database |
| New: category tooltips | — | Hover ℹ️ on every requirement explaining *why that category matters* (Udyam, GST, PAN, Make in India, EPFO/ESIC, Startup India, NSIC, OEM) |

Streamlit is no longer the whole application — it's a UI that calls your API, the same relationship a React frontend would have. That's the architectural claim that matters for the pitch: separation of concerns, a real API layer, a real database. Cutting React for Streamlit is cosmetic; keeping Streamlit stateless and API-driven is structural, and that's what changed here.

**Cut, deliberately, and why:**
- **PostgreSQL → SQLite.** Same "we use a real database" claim, same SQL — but it's one file, no server process to start, no connection string to get wrong on demo day.
- **Object storage** — not added. PDFs are processed in-memory per verification and never need to persist as files.
- **OCR** — not added. GeM tenders/bids are text-based PDFs, not scanned images; OCR would solve a problem you don't have.

## Cost — is any of this paid?

**No.** FastAPI, Uvicorn, SQLite, Streamlit, and every Python package in `requirements.txt` are free and open-source — nothing here has a license fee or usage cap. The **only** possible cost anywhere in this stack is Gemini API usage once you exceed Google's free tier at [aistudio.google.com](https://aistudio.google.com) — which is generous enough for a hackathon demo. Everything else runs entirely on your own machine.

## Architecture

```
┌─────────────────────┐      HTTP (JSON + file upload)      ┌──────────────────────┐
│   Streamlit          │ ───────────────────────────────────▶│   FastAPI backend     │
│   frontend/app.py     │◀─────────────────────────────────── │   backend/main.py     │
│   (port 8501)         │              JSON / PDF bytes        │   (port 8000)         │
└─────────────────────┘                                       └──────────┬───────────┘
                                                                          │
                                          ┌───────────────────────────────┼───────────────────────────┐
                                          ▼                               ▼                             ▼
                                 verification_service.py            rules.py                    database.py
                                 (PDFplumber + Gemini calls,      (deterministic rule       (SQLite — audit_trail.db,
                                  prompt-injection guardrail,      engine — your V1 file,       mock_portal_data.json)
                                  PDF report generation)           unchanged interface)
```

## Project layout

```
gem-v2/
├── README.md
├── backend/
│   ├── main.py                  FastAPI app — all endpoints
│   ├── verification_service.py  PDF extraction, Gemini calls, guardrail, PDF report generation
│   ├── rules.py                 ⚠️ REPLACE with your real V1 rules.py — interface unchanged
│   ├── mock_portal_data.json    ⚠️ REPLACE with your real V1 mock data (sample data included for testing)
│   ├── requirement_help.py      "Why does this matter" tooltip text per requirement category
│   ├── database.py              SQLite persistence (stdlib sqlite3, no ORM)
│   ├── schemas.py                Pydantic request/response models
│   ├── config.py                Reads .env
│   ├── requirements.txt
│   └── .env.example              Copy to .env and fill in your Gemini key
└── frontend/
    ├── app.py                   Streamlit UI — calls the backend, renders results
    └── requirements.txt
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# open .env and paste your free Gemini key from https://aistudio.google.com

# Drop your real V1 files in here, replacing the placeholders:
#   - rules.py            (your deterministic rule engine)
#   - mock_portal_data.json (your real mock portal database)

uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` — FastAPI auto-generates interactive API docs, useful for testing `/verify` directly without the frontend.

### 2. Frontend

In a **second terminal**:

```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

streamlit run app.py
```

Opens at `http://localhost:8501`. It talks to the backend at `http://localhost:8000` by default — override with `BACKEND_URL` if you deploy them separately:

```bash
BACKEND_URL=http://your-backend-host:8000 streamlit run app.py
```

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/verify` | Upload tender + vendor PDFs + PAN, runs the full pipeline, returns JSON |
| POST | `/audit` | Save an officer decision to the audit trail (SQLite) |
| GET | `/audit` | List all audit entries — requires `x-officer-code` header |
| GET | `/audit/{id}/report` | Regenerate the PDF report for a saved entry — requires `x-officer-code` header |
| POST | `/report/preview` | Generate a PDF report before saving (ad hoc) |
| GET | `/portal-database` | View the mock portal database — requires `x-officer-code` header |
| GET | `/health` | Health check |

Default officer access code is `officer2026` (set in `.env` as `OFFICER_ACCESS_CODE` — change it before a real demo, same as V1).

## Requirement category tooltips

Every requirement card in the dashboard now has a small **ℹ️** next to its status — hover it and a judge unfamiliar with GeM jargon gets a one-sentence explanation of why that category (Udyam, GST, PAN, Make in India, EPFO/ESIC, Startup India, NSIC, OEM) matters for eligibility. Edit the text in `backend/requirement_help.py`.

## What was tested before handing this off

- FastAPI app imports and all routes register correctly.
- `POST /audit` → SQLite insert → `GET /audit` (with and without the officer header, confirming the 401 gate works).
- `GET /audit/{id}/report` and `POST /report/preview` both generate a valid PDF (rendered and visually checked).
- `rules.py` and `mock_portal_data.json` are placeholders with sample data — **the Gemini calls themselves (`/verify` end-to-end) haven't been tested against the live API from this environment**, since network access here doesn't reach Google's API. Test `/verify` yourself once your real key is in `.env`.
