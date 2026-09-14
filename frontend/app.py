"""
GeM Bid Compliance Verification Platform — V2 frontend.

This is now a thin Streamlit CLIENT: all verification logic, Gemini calls,
the rule engine, the database and PDF generation live in the FastAPI backend
(see backend/main.py). This file only collects input, calls the API, and
renders the response.

Run with:  streamlit run app.py
Requires the backend running first:  uvicorn main:app --reload --port 8000
"""
import os
from datetime import datetime

import requests
import streamlit as st

BACKEND_URL = st.secrets.get("BACKEND_URL", os.environ.get("BACKEND_URL", "http://localhost:8000"))
st.set_page_config(page_title="GeM Bid Compliance Verification", page_icon="🏛", layout="wide")

st.markdown("""
<style>
    :root {
        --gem-navy: #0b3d66;
        --gem-blue: #1668a3;
        --gem-gray: #f4f6f8;
    }
    .stApp { background-color: #fafbfc; }
    h1 { color: var(--gem-navy); font-weight: 700; }
    h3, h4 { color: var(--gem-navy); }
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e0e4e8;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricValue"] { color: var(--gem-navy); font-weight: 700; }
    .stButton > button[kind="primary"] {
        background-color: var(--gem-blue);
        border: none;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.55em 1.4em;
    }
    .stButton > button[kind="primary"]:hover { background-color: var(--gem-navy); }
    div[data-testid="stTabs"] button { font-weight: 600; }
    .req-card {
        background-color: white;
        border: 1px solid #e5e8eb;
        border-left: 4px solid #cfd6dc;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .req-card.pass { border-left-color: #1e9e58; }
    .req-card.fail { border-left-color: #d64545; }
    .req-card.inconsistent { border-left-color: #d6a545; }
    .req-card.unverifiable { border-left-color: #9aa4ad; }
    .badge {
        display: inline-block;
        font-size: 0.72em;
        font-weight: 600;
        padding: 1px 8px;
        border-radius: 10px;
        background-color: var(--gem-gray);
        color: var(--gem-navy);
        margin-left: 6px;
    }
    /* Native browser tooltip via the title attribute on this span — no JS needed */
    .help-tip {
        display: inline-block;
        cursor: help;
        margin-left: 6px;
        color: #9aa4ad;
        font-size: 0.85em;
        border: 1px solid #cfd6dc;
        border-radius: 50%;
        width: 15px;
        height: 15px;
        text-align: center;
        line-height: 14px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛 AI-Powered Bid Compliance Verification Platform")
st.caption("SIH26100 — MVP Demo v2 | GeM Procurement | Decision-support tool — final call stays with the Procurement Officer")
st.markdown(
    f'<span style="color:#5a6570; font-size:0.85em;">Backend: '
    f'<span style="color:#1668a3; font-weight:600;">{BACKEND_URL}</span></span>',
    unsafe_allow_html=True,
)

st.warning(
    "**Simulated data notice:** Udyam, GSTN, PAN, EPFO/ESIC, Startup India, NSIC "
    "and Blacklist checks in this demo use a MOCK local database, not live government APIs. Real "
    "Udyam/GSTN/DigiLocker integration requires official government registration/MOUs that aren't "
    "accessible for a hackathon build.",
    icon="⚠️"
)


def api_get(path, **kwargs):
    return requests.get(f"{BACKEND_URL}{path}", timeout=60, **kwargs)


def api_post(path, **kwargs):
    return requests.post(f"{BACKEND_URL}{path}", timeout=180, **kwargs)


tab1, tab2 = st.tabs(["🔍 Run Verification", "📜 Audit Trail"])

# ---------------- TAB 1: VERIFICATION ----------------
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Step 1: Upload Tender Document")
        tender_file = st.file_uploader("Tender / RFP PDF", type=["pdf"], key="tender")
    with col2:
        st.subheader("Step 2: Upload Vendor Bid Document")
        vendor_file = st.file_uploader("Vendor bid submission PDF", type=["pdf"], key="vendor")

    st.subheader("Step 3: Enter Bidder PAN (for portal lookup)")
    bidder_pan = st.text_input("Bidder PAN", placeholder="e.g. AABCU1234C")

    run_col, clear_col = st.columns([3, 1])
    run_clicked = run_col.button("🔍 Run Verification", type="primary", use_container_width=True)
    if clear_col.button("🔄 New Verification", use_container_width=True):
        st.session_state.pop("verification", None)
        st.rerun()

    if run_clicked:
        if not tender_file or not vendor_file:
            st.warning("Please upload both the tender and vendor bid PDFs.")
        elif not bidder_pan.strip():
            st.warning("Please enter the bidder's PAN.")
        else:
            try:
                with st.spinner("Running verification pipeline (this calls the backend API)..."):
                    files = {
                        "tender_file": (tender_file.name, tender_file.getvalue(), "application/pdf"),
                        "vendor_file": (vendor_file.name, vendor_file.getvalue(), "application/pdf"),
                    }
                    data = {"bidder_pan": bidder_pan.strip()}
                    resp = api_post("/verify", files=files, data=data)
            except requests.exceptions.ConnectionError:
                st.error(f"⚠️ Couldn't reach the backend at {BACKEND_URL}. Is `uvicorn main:app` running?")
                resp = None

            if resp is not None:
                if resp.status_code != 200:
                    st.error(f"Backend error ({resp.status_code}): {resp.text}")
                else:
                    result = resp.json()
                    if result.get("blocked"):
                        if result.get("error"):
                            st.error("The AI response couldn't be parsed. Raw output below for debugging:")
                            st.code(result.get("raw_response", ""))
                        else:
                            st.error(f"⚠️ **{result.get('block_reason', 'Verification blocked.')}**")
                    else:
                        if result.get("alignment_warning"):
                            st.warning(f"ℹ️ {result['alignment_warning']} Proceeding, but please double-check the uploaded files look right below.")

                        if result.get("injection_hits"):
                            st.error(f"🛡 **Guardrail triggered:** the vendor's bid document contains suspicious phrasing that looks "
                                     f"like an attempt to manipulate the AI's output (matched: {', '.join(result['injection_hits'])}). "
                                     f"This is flagged for the officer and factored into the AI's own analysis below.")

                        resolved = result.get("rule_engine_resolved_count", 0)
                        total = result.get("checklist_total_count", 0)
                        if resolved:
                            st.info(f"⚙️ **Rule Engine:** resolved {resolved} of {total} requirements "
                                    f"deterministically (no AI call needed for these) — {total - resolved} remaining "
                                    f"require AI interpretation.", icon="⚙️")

                        st.session_state["verification"] = {"result": result, "saved": False}

    # ---- Display block: reads from session_state, survives reruns (e.g. clicking Save) ----
    if "verification" in st.session_state:
        v = st.session_state["verification"]
        result = v["result"]
        bidder_name = result.get("bidder_name", "Unknown bidder")
        bidder_pan_clean = result.get("bidder_pan", "")
        score = result.get("compliance_score", 0)
        risk = result.get("risk_level", "Unknown")
        requirement_results = result.get("requirement_results", [])
        rule_results = result.get("rule_results", [])
        flags = result.get("flags", [])

        st.divider()
        st.subheader(f"📊 Compliance Dashboard — {bidder_name}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Compliance Score", f"{score}/100")
        risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(risk, "⚪")
        m2.metric("Risk Level", f"{risk_emoji} {risk}")
        m3.metric("Requirements Checked", len(requirement_results))

        if flags:
            st.error("**🚩 Red Flags Detected:**\n" + "\n".join(f"- {f}" for f in flags))

        st.info(f"**🤖 AI Recommendation (advisory only):** {result.get('recommendation', '')}")

        st.markdown("#### Requirement-by-Requirement Status")
        rule_engine_requirements = {r["requirement"] for r in rule_results} if rule_results else set()
        status_class = {"PASS": "pass", "FAIL": "fail", "INCONSISTENT": "inconsistent", "UNVERIFIABLE": "unverifiable"}
        status_icon = {"PASS": "🟢", "FAIL": "🔴", "INCONSISTENT": "🟡", "UNVERIFIABLE": "⚪"}
        for r in requirement_results:
            status = r.get("status", "UNVERIFIABLE")
            icon = status_icon.get(status, "⚪")
            css_class = status_class.get(status, "unverifiable")
            source_badge = "⚙️ Rule Engine" if r.get("requirement") in rule_engine_requirements else "🤖 AI"
            category_help = (r.get("category_help") or "").replace('"', "&quot;")
            tooltip_html = f'<span class="help-tip" title="{category_help}">?</span>' if category_help else ""
            st.markdown(
                f"""<div class="req-card {css_class}">
                    <b>{icon} {r.get('requirement', '')}</b> — {status}{tooltip_html}
                    <span class="badge">{source_badge}</span><br>
                    <span style="color:#5a6570; font-size:0.9em;">{r.get('evidence', '')}</span>
                </div>""",
                unsafe_allow_html=True
            )

        st.divider()
        st.markdown("#### 👤 Procurement Officer's Final Decision")
        st.caption("The AI never decides this — it's logged separately for the audit trail.")
        decision = st.radio("Officer decision:", ["Not yet decided", "Qualify bidder", "Disqualify bidder", "Hold for further review"], key="decision")
        notes = st.text_area(
            "Officer notes (optional)",
            key="officer_notes",
            placeholder="e.g. Hold for review — pending EMD clarification from bidder.",
            height=90,
        )

        if v.get("saved"):
            st.success("✅ Saved to audit trail.")

        save_col, pdf_col = st.columns(2)
        if save_col.button("💾 Save decision to audit trail", use_container_width=True):
            payload = {
                "bidder_pan": bidder_pan_clean,
                "bidder_name": bidder_name,
                "compliance_score": score,
                "risk_level": risk,
                "flags": flags,
                "ai_recommendation": result.get("recommendation", ""),
                "officer_decision": decision,
                "officer_notes": notes,
                "requirement_results": requirement_results,
                "rule_results": rule_results,
            }
            save_resp = api_post("/audit", json=payload)
            if save_resp.status_code == 200:
                st.session_state["verification"]["saved"] = True
                st.rerun()
            else:
                st.error(f"Couldn't save to audit trail: {save_resp.text}")

        report_payload = {
            "bidder_pan": bidder_pan_clean,
            "bidder_name": bidder_name,
            "compliance_score": score,
            "risk_level": risk,
            "flags": flags,
            "recommendation": result.get("recommendation", ""),
            "requirement_results": requirement_results,
            "rule_results": rule_results,
            "officer_decision": decision,
            "officer_notes": notes,
        }
        pdf_resp = api_post("/report/preview", json=report_payload)
        if pdf_resp.status_code == 200:
            pdf_col.download_button(
                "📄 Download compliance report (PDF)",
                data=pdf_resp.content,
                file_name=f"compliance_report_{bidder_pan_clean}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            pdf_col.caption("PDF preview unavailable — backend error generating report.")

# ---------------- TAB 2: AUDIT TRAIL ----------------
with tab2:
    st.subheader("📜 Verification Audit Trail")
    st.caption("🔒 Officer-only access. In a real deployment this would use proper government SSO/role-based login — "
               "this access code is a simplified stand-in to demonstrate that audit data must be access-controlled, not public.")

    access_code = st.text_input("Enter Officer Access Code to view audit trail:", type="password")
    if not access_code:
        st.stop()

    headers = {"x-officer-code": access_code}
    resp = api_get("/audit", headers=headers)
    if resp.status_code == 401:
        st.error("Incorrect access code.")
        st.stop()
    elif resp.status_code != 200:
        st.error(f"Backend error ({resp.status_code}): {resp.text}")
        st.stop()

    log = resp.json()
    if not log:
        st.caption("No verifications logged yet. Run a verification in the first tab and save a decision.")
    else:
        for entry in log:  # already newest-first from the backend
            with st.expander(f"{entry['timestamp']} — {entry['bidder_name']} — Score: {entry['compliance_score']} — {entry['officer_decision']}"):
                st.json(entry)
                report_resp = api_get(f"/audit/{entry['id']}/report", headers=headers)
                if report_resp.status_code == 200:
                    st.download_button(
                        "📄 Download PDF report",
                        data=report_resp.content,
                        file_name=f"compliance_report_{entry['bidder_pan']}_{entry['id']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{entry['id']}",
                    )

    st.divider()
    with st.expander("📂 View the mock government portal database used in this demo"):
        db_resp = api_get("/portal-database", headers=headers)
        if db_resp.status_code == 200:
            st.json(db_resp.json())
