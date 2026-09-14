"""
SQLite persistence for the audit trail. Deliberately plain stdlib sqlite3
(no ORM) — a hackathon MVP doesn't need SQLAlchemy's complexity, and this is
already a real relational database with real SQL, which is the architectural
claim that matters for the pitch.

SQLite ships with Python — this is zero additional cost and zero server setup,
unlike Postgres which needs a running server process, connection strings and
credentials to manage.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    bidder_pan TEXT NOT NULL,
    bidder_name TEXT NOT NULL,
    compliance_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    flags_json TEXT NOT NULL,
    ai_recommendation TEXT NOT NULL,
    officer_decision TEXT NOT NULL,
    officer_notes TEXT NOT NULL DEFAULT '',
    requirement_results_json TEXT NOT NULL DEFAULT '[]',
    rule_results_json TEXT NOT NULL DEFAULT '[]'
);
"""


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute(SCHEMA)


def insert_audit_entry(
    bidder_pan: str,
    bidder_name: str,
    compliance_score: int,
    risk_level: str,
    flags: list,
    ai_recommendation: str,
    officer_decision: str,
    officer_notes: str,
    requirement_results: list,
    rule_results: list,
) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO audit_entries (
                timestamp, bidder_pan, bidder_name, compliance_score, risk_level,
                flags_json, ai_recommendation, officer_decision, officer_notes,
                requirement_results_json, rule_results_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp, bidder_pan, bidder_name, compliance_score, risk_level,
                json.dumps(flags), ai_recommendation, officer_decision, officer_notes,
                json.dumps(requirement_results), json.dumps(rule_results),
            ),
        )
        entry_id = cursor.lastrowid
    return get_audit_entry(entry_id)


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["flags"] = json.loads(d.pop("flags_json"))
    d["requirement_results"] = json.loads(d.pop("requirement_results_json"))
    d["rule_results"] = json.loads(d.pop("rule_results_json"))
    return d


def get_audit_entry(entry_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM audit_entries WHERE id = ?", (entry_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_audit_entries() -> list:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM audit_entries ORDER BY id DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


def load_portal_database() -> dict:
    from config import MOCK_PORTAL_PATH
    with open(MOCK_PORTAL_PATH, "r") as f:
        return json.load(f)
