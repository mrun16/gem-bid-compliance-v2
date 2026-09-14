"""
GeM Bid Compliance Verification Platform — V2 polished frontend.

Thin Streamlit client:
- Collects tender + vendor documents
- Sends them to the FastAPI backend
- Displays compliance results
- Allows officer decision + audit trail access
- Downloads generated PDF reports

All verification logic, rule engine, Gemini calls, mock government
database, audit database and PDF generation remain in the backend.

Run locally:
    streamlit run app.py
"""

import os
from datetime import datetime

import requests
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_URL = st.secrets.get(
    "BACKEND_URL",
    os.environ.get("BACKEND_URL", "http://localhost:8000"),
)

st.set_page_config(
    page_title="GeM Bid Compliance",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #f5f7fa;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Hide default Streamlit menu/footer */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    /* ---------- HERO ---------- */

    .hero {
        background: linear-gradient(135deg, #073763 0%, #0d5b91 55%, #1675ad 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 18px;
        margin-bottom: 1.4rem;
        box-shadow: 0 8px 25px rgba(7, 55, 99, 0.16);
    }

    .hero-kicker {
        color: #b9dfff;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .hero-title {
        color: white;
        font-size: 2.15rem;
        line-height: 1.15;
        font-weight: 750;
        margin: 0;
    }

    .hero-subtitle {
        color: #e2f1fb;
        font-size: 1rem;
        margin-top: 0.7rem;
        max-width: 850px;
        line-height: 1.55;
    }

    .hero-note {
        margin-top: 1rem;
        color: #d7ecfa;
        font-size: 0.84rem;
    }

    /* ---------- FEATURE CHIPS ---------- */

    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 1rem 0 1.5rem 0;
    }

    .chip {
        background: white;
        border: 1px solid #dce4eb;
        color: #244b68;
        padding: 7px 13px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
    }

    /* ---------- NOTICE ---------- */

    .mock-notice {
        background: #fff8e6;
        border: 1px solid #f0d58a;
        border-left: 5px solid #d79b19;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 1.5rem;
        color: #624d16;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    /* ---------- SECTION HEADERS ---------- */

    .section-label {
        color: #1668a3;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .section-title {
        color: #0b3d66;
        font-size: 1.35rem;
        font-weight: 750;
        margin-bottom: 0.2rem;
    }

    .section-description {
        color: #647484;
        font-size: 0.88rem;
        margin-bottom: 1rem;
    }

    /* ---------- UPLOAD CARDS ---------- */

    .upload-card {
        background: white;
        border: 1px solid #dfe6ec;
        border-radius: 14px;
        padding: 1.15rem 1.25rem 0.75rem 1.25rem;
        min-height: 180px;
        box-shadow: 0 3px 12px rgba(21, 48, 72, 0.04);
    }

    .upload-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: #e8f3fb;
        color: #12649b;
        font-weight: 800;
        margin-right: 8px;
    }

    .upload-title {
        color: #173f5f;
        font-size: 1rem;
        font-weight: 750;
    }

    .upload-description {
        color: #6b7885;
        font-size: 0.82rem;
        line-height: 1.4;
        margin: 0.5rem 0 0.8rem 0;
    }

    /* ---------- PAN CARD ---------- */

    .pan-card {
        background: white;
        border: 1px solid #dfe6ec;
        border-radius: 14px;
        padding: 1.2rem 1.3rem;
        margin-top: 1rem;
        box-shadow: 0 3px 12px rgba(21, 48, 72, 0.04);
    }

    /* ---------- METRICS ---------- */

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #dfe6ec;
        border-radius: 13px;
        padding: 1rem 1.1rem;
        box-shadow: 0 3px 12px rgba(21, 48, 72, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        color: #647484;
        font-size: 0.8rem;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #0b3d66;
        font-weight: 800;
    }

    /* ---------- RESULT HEADER ---------- */

    .result-header {
        background: white;
        border: 1px solid #dfe6ec;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 3px 12px rgba(21, 48, 72, 0.04);
    }

    .result-kicker {
        color: #73808c;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.7px;
        text-transform: uppercase;
    }

    .result-name {
        color: #0b3d66;
        font-size: 1.45rem;
        font-weight: 800;
        margin-top: 0.25rem;
    }

    .pan-text {
        color: #687683;
        font-size: 0.84rem;
    }

    /* ---------- REQUIREMENT CARDS ---------- */

    .req-card {
        background: white;
        border: 1px solid #e0e6eb;
        border-left: 5px solid #aab4bd;
        border-radius: 9px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.55rem;
        box-shadow: 0 2px 7px rgba(21, 48, 72, 0.025);
    }

    .req-card.pass {
        border-left-color: #239b58;
    }

    .req-card.fail {
        border-left-color: #d64545;
    }

    .req-card.inconsistent {
        border-left-color: #d49a27;
    }

    .req-card.unverifiable {
        border-left-color: #929da7;
    }

    .req-title {
        color: #183f5d;
        font-weight: 750;
        font-size: 0.92rem;
    }

    .req-status {
        font-size: 0.76rem;
        font-weight: 800;
        margin-left: 5px;
    }

    .req-evidence {
        color: #687783;
        font-size: 0.82rem;
        line-height: 1.45;
        margin-top: 0.35rem;
    }

    .badge {
        display: inline-block;
        background: #edf3f7;
        color: #38566d;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.68rem;
        font-weight: 700;
        margin-left: 7px;
    }

    /* ---------- SUMMARY CARDS ---------- */

    .summary-card {
        background: white;
        border: 1px solid #dfe6ec;
        border-radius: 13px;
        padding: 1.15rem 1.2rem;
        min-height: 125px;
        box-shadow: 0 3px 12px rgba(21, 48, 72, 0.04);
    }

    .summary-label {
        color: #73808c;
        font-size: 0.73rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.7px;
    }

    .summary-value {
        color: #0b3d66;
        font-size: 1.5rem;
        font-weight: 800;
        margin-top: 0.25rem;
    }

    .summary-small {
        color: #687783;
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }

    /* ---------- OFFICER CARD ---------- */

    .officer-card {
        background: #f1f7fb;
        border: 1px solid #cfe2ee;
        border-radius: 13px;
        padding: 1.1rem 1.25rem;
        margin-top: 1rem;
    }

    .officer-title {
        color: #0b3d66;
        font-weight: 800;
        font-size: 1rem;
    }

    .officer-text {
        color: #5e7080;
        font-size: 0.82rem;
        margin-top: 0.25rem;
    }

    /* ---------- AUDIT ---------- */

    .audit-banner {
        background: white;
        border: 1px solid #dfe6ec;
        border-radius: 13px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        color: #566977;
        font-size: 0.84rem;
        line-height: 1.5;
    }

    /* ---------- BUTTONS ---------- */

    .stButton > button {
        border-radius: 9px;
        font-weight: 700;
        min-height: 42px;
    }

    .stButton > button[kind="primary"] {
        background: #1268a3;
        border: 0;
    }

    .stButton > button[kind="primary"]:hover {
        background: #0b3d66;
        border: 0;
    }

    /* ---------- DIVIDERS ---------- */

    hr {
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        border-color: #e1e6ea;
    }

    /* ---------- FILE UPLOADER ---------- */

    div[data-testid="stFileUploader"] {
        background: #fafcfd;
        border-radius: 9px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API HELPERS
# ============================================================

def api_get(path, **kwargs):
    return requests.get(
        f"{BACKEND_URL}{path}",
        timeout=60,
        **kwargs,
    )


def api_post(path, **kwargs):
    return requests.post(
        f"{BACKEND_URL}{path}",
        timeout=180,
        **kwargs,
    )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">SIH26100 • GeM Procurement • MVP Demo V2</div>
        <div class="hero-title">
            AI-Powered Bid Compliance<br>
            Verification Platform
        </div>
        <div class="hero-subtitle">
            An intelligent decision-support system that checks bidder
            eligibility, identifies inconsistencies and highlights compliance
            risks before tender evaluation.
        </div>
        <div class="hero-note">
            Final qualification or disqualification remains with the
            Procurement Officer.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FEATURE CHIPS
# ============================================================

st.markdown(
    """
    <div class="chip-row">
        <div class="chip">⚙️ Rule Engine</div>
        <div class="chip">🤖 AI Analysis</div>
        <div class="chip">🏛️ Government Checks</div>
        <div class="chip">🚩 Risk Detection</div>
        <div class="chip">📜 Audit Trail</div>
        <div class="chip">📄 PDF Report</div>
        <div class="chip">🛡️ AI Guardrails</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIMULATED DATA NOTICE
# ============================================================

st.markdown(
    """
    <div class="mock-notice">
        <b>⚠️ Simulated data notice:</b>
        Udyam, GSTN, PAN, EPFO/ESIC, Startup India, NSIC and Blacklist
        checks in this demo use a <b>MOCK local database</b>, not live
        government APIs. Real Udyam/GSTN/DigiLocker integration requires
        official government registration/MOUs that aren't accessible for
        a hackathon build.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TABS
# ============================================================

tab1, tab2 = st.tabs(
    [
        "🔍  Run Verification",
        "📜  Protected Audit Trail",
    ]
)


# ============================================================
# TAB 1 — VERIFICATION
# ============================================================

with tab1:

    st.markdown(
        """
        <div class="section-label">Verification workflow</div>
        <div class="section-title">Check a bidder's compliance</div>
        <div class="section-description">
            Upload the tender and bidder submission, then provide the PAN
            used for the simulated government-portal lookup.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # DOCUMENT UPLOADS
    # --------------------------------------------------------

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class="upload-card">
                <span class="upload-number">1</span>
                <span class="upload-title">Tender / RFP Document</span>
                <div class="upload-description">
                    Upload the tender PDF containing eligibility,
                    technical and statutory requirements.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tender_file = st.file_uploader(
            "Tender / RFP PDF",
            type=["pdf"],
            key="tender",
            label_visibility="collapsed",
        )

        if tender_file:
            st.success(f"✓ {tender_file.name}")

    with col2:
        st.markdown(
            """
            <div class="upload-card">
                <span class="upload-number">2</span>
                <span class="upload-title">Vendor Bid Submission</span>
                <div class="upload-description">
                    Upload the bidder's submitted PDF for document
                    evidence and consistency analysis.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        vendor_file = st.file_uploader(
            "Vendor bid submission PDF",
            type=["pdf"],
            key="vendor",
            label_visibility="collapsed",
        )

        if vendor_file:
            st.success(f"✓ {vendor_file.name}")

    # --------------------------------------------------------
    # PAN
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="pan-card">
            <div class="section-label">Portal lookup</div>
            <div class="section-title">3. Identify the bidder</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    bidder_pan = st.text_input(
        "Bidder PAN",
        placeholder="Example: AABCU1234C",
        key="bidder_pan_input",
    )

    # --------------------------------------------------------
    # ACTION BUTTONS
    # --------------------------------------------------------

    st.markdown("<br>", unsafe_allow_html=True)

    run_col, clear_col = st.columns([3, 1])

    run_clicked = run_col.button(
        "🔍  Run Compliance Verification",
        type="primary",
        use_container_width=True,
    )

    clear_clicked = clear_col.button(
        "↻  New Verification",
        use_container_width=True,
    )

    if clear_clicked:
        st.session_state.pop("verification", None)
        st.session_state.pop("decision", None)
        st.session_state.pop("officer_notes", None)
        st.rerun()

    # --------------------------------------------------------
    # RUN API
    # --------------------------------------------------------

    if run_clicked:

        if not tender_file or not vendor_file:
            st.warning(
                "Please upload both the tender PDF and vendor bid PDF."
            )

        elif not bidder_pan.strip():
            st.warning(
                "Please enter the bidder's PAN."
            )

        else:

            try:

                with st.spinner(
                    "Running verification pipeline — extracting documents, "
                    "checking rules and analysing compliance..."
                ):

                    files = {
                        "tender_file": (
                            tender_file.name,
                            tender_file.getvalue(),
                            "application/pdf",
                        ),
                        "vendor_file": (
                            vendor_file.name,
                            vendor_file.getvalue(),
                            "application/pdf",
                        ),
                    }

                    data = {
                        "bidder_pan": bidder_pan.strip()
                    }

                    resp = api_post(
                        "/verify",
                        files=files,
                        data=data,
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "⚠️ Unable to reach the verification backend. "
                    "Please check that the deployed backend is available."
                )

                resp = None

            except requests.exceptions.Timeout:

                st.error(
                    "⏱️ The verification request timed out. "
                    "Please try again."
                )

                resp = None

            except Exception as exc:

                st.error(
                    f"Unexpected connection error: {exc}"
                )

                resp = None

            # ------------------------------------------------
            # RESPONSE
            # ------------------------------------------------

            if resp is not None:

                if resp.status_code != 200:

                    st.error(
                        f"Backend error ({resp.status_code}): {resp.text}"
                    )

                else:

                    result = resp.json()

                    if result.get("blocked"):

                        if result.get("error"):

                            st.error(
                                "The AI response could not be parsed."
                            )

                            st.code(
                                result.get("raw_response", "")
                            )

                        else:

                            st.error(
                                f"⚠️ {result.get(
                                    'block_reason',
                                    'Verification blocked.'
                                )}"
                            )

                    else:

                        if result.get("alignment_warning"):

                            st.warning(
                                f"ℹ️ {result['alignment_warning']} "
                                "Please double-check the uploaded documents."
                            )

                        if result.get("injection_hits"):

                            st.error(
                                "🛡️ **AI Guardrail Triggered:** "
                                "The vendor document contains suspicious "
                                "phrasing that may attempt to manipulate "
                                "the AI output. This has been flagged for "
                                "the Procurement Officer."
                            )

                        resolved = result.get(
                            "rule_engine_resolved_count",
                            0,
                        )

                        total = result.get(
                            "checklist_total_count",
                            0,
                        )

                        if resolved:

                            remaining = total - resolved

                            st.info(
                                f"⚙️ **Rule Engine:** {resolved} of "
                                f"{total} requirements were resolved "
                                f"deterministically. {remaining} "
                                f"require AI interpretation."
                            )

                        st.session_state["verification"] = {
                            "result": result,
                            "saved": False,
                        }


    # ========================================================
    # DISPLAY RESULT
    # ========================================================

    if "verification" in st.session_state:

        verification = st.session_state["verification"]
        result = verification["result"]

        bidder_name = result.get(
            "bidder_name",
            "Unknown bidder",
        )

        bidder_pan_clean = result.get(
            "bidder_pan",
            "",
        )

        score = result.get(
            "compliance_score",
            0,
        )

        risk = result.get(
            "risk_level",
            "Unknown",
        )

        requirement_results = result.get(
            "requirement_results",
            [],
        )

        rule_results = result.get(
            "rule_results",
            [],
        )

        flags = result.get(
            "flags",
            [],
        )

        # ----------------------------------------------------
        # RESULT HEADER
        # ----------------------------------------------------

        st.divider()

        st.markdown(
            f"""
            <div class="result-header">
                <div class="result-kicker">
                    Verification completed
                </div>
                <div class="result-name">
                    {bidder_name}
                </div>
                <div class="pan-text">
                    PAN: {bidder_pan_clean}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # SUMMARY METRICS
        # ----------------------------------------------------

        m1, m2, m3 = st.columns(3)

        m1.metric(
            "Compliance Score",
            f"{score}/100",
        )

        risk_emoji = {
            "Low": "🟢",
            "Medium": "🟡",
            "High": "🔴",
        }.get(
            risk,
            "⚪",
        )

        m2.metric(
            "Risk Level",
            f"{risk_emoji} {risk}",
        )

        m3.metric(
            "Requirements Checked",
            len(requirement_results),
        )

        # ----------------------------------------------------
        # RED FLAGS
        # ----------------------------------------------------

        if flags:

            st.markdown("<br>", unsafe_allow_html=True)

            st.error(
                "**🚩 Red Flags Detected**\n\n"
                + "\n".join(
                    f"- {flag}"
                    for flag in flags
                )
            )

        # ----------------------------------------------------
        # AI RECOMMENDATION
        # ----------------------------------------------------

        recommendation = result.get(
            "recommendation",
            "",
        )

        if recommendation:

            st.info(
                f"🤖 **AI Recommendation — Advisory Only**\n\n"
                f"{recommendation}"
            )

        # ----------------------------------------------------
        # REQUIREMENTS
        # ----------------------------------------------------

        st.markdown(
            """
            <div class="section-label">Detailed results</div>
            <div class="section-title">
                Requirement-by-Requirement Status
            </div>
            <div class="section-description">
                Each requirement is labelled as verified by deterministic
                rules or interpreted by AI.
            </div>
            """,
            unsafe_allow_html=True,
        )

        rule_engine_requirements = {
            r.get("requirement")
            for r in rule_results
        }

        status_class = {
            "PASS": "pass",
            "FAIL": "fail",
            "INCONSISTENT": "inconsistent",
            "UNVERIFIABLE": "unverifiable",
        }

        status_icon = {
            "PASS": "🟢",
            "FAIL": "🔴",
            "INCONSISTENT": "🟡",
            "UNVERIFIABLE": "⚪",
        }

        for requirement in requirement_results:

            status = requirement.get(
                "status",
                "UNVERIFIABLE",
            )

            icon = status_icon.get(
                status,
                "⚪",
            )

            css_class = status_class.get(
                status,
                "unverifiable",
            )

            source_badge = (
                "⚙️ Rule Engine"
                if requirement.get("requirement")
                in rule_engine_requirements
                else "🤖 AI"
            )

            requirement_name = requirement.get(
                "requirement",
                "Requirement",
            )

            evidence = requirement.get(
                "evidence",
                "",
            )

            st.markdown(
                f"""
                <div class="req-card {css_class}">
                    <div>
                        <span class="req-title">
                            {icon} {requirement_name}
                        </span>
                        <span class="req-status">
                            {status}
                        </span>
                        <span class="badge">
                            {source_badge}
                        </span>
                    </div>
                    <div class="req-evidence">
                        {evidence}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # OFFICER DECISION
        # ----------------------------------------------------

        st.divider()

        st.markdown(
            """
            <div class="officer-card">
                <div class="officer-title">
                    👤 Procurement Officer Review
                </div>
                <div class="officer-text">
                    The AI provides decision support only.
                    The final qualification/disqualification decision
                    is made and recorded separately by the authorized
                    Procurement Officer.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        decision = st.radio(
            "Officer decision",
            [
                "Not yet decided",
                "Qualify bidder",
                "Disqualify bidder",
                "Hold for further review",
            ],
            key="decision",
            horizontal=True,
        )

        notes = st.text_area(
            "Officer notes (optional)",
            key="officer_notes",
            placeholder=(
                "Example: Hold for review — pending clarification "
                "from bidder."
            ),
            height=90,
        )

        if verification.get("saved"):

            st.success(
                "✅ Decision successfully saved to the protected audit trail."
            )

        # ----------------------------------------------------
        # SAVE + PDF
        # ----------------------------------------------------

        save_col, pdf_col = st.columns(2)

        if save_col.button(
            "💾  Save Officer Decision",
            use_container_width=True,
        ):

            payload = {
                "bidder_pan": bidder_pan_clean,
                "bidder_name": bidder_name,
                "compliance_score": score,
                "risk_level": risk,
                "flags": flags,
                "ai_recommendation": recommendation,
                "officer_decision": decision,
                "officer_notes": notes,
                "requirement_results": requirement_results,
                "rule_results": rule_results,
            }

            try:

                save_resp = api_post(
                    "/audit",
                    json=payload,
                )

                if save_resp.status_code == 200:

                    st.session_state[
                        "verification"
                    ]["saved"] = True

                    st.rerun()

                else:

                    st.error(
                        "Could not save the decision: "
                        + save_resp.text
                    )

            except Exception as exc:

                st.error(
                    f"Could not save the audit record: {exc}"
                )

        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        report_payload = {
            "bidder_pan": bidder_pan_clean,
            "bidder_name": bidder_name,
            "compliance_score": score,
            "risk_level": risk,
            "flags": flags,
            "recommendation": recommendation,
            "requirement_results": requirement_results,
            "rule_results": rule_results,
            "officer_decision": decision,
            "officer_notes": notes,
        }

        try:

            pdf_resp = api_post(
                "/report/preview",
                json=report_payload,
            )

            if pdf_resp.status_code == 200:

                pdf_col.download_button(
                    "📄  Download Compliance Report",
                    data=pdf_resp.content,
                    file_name=(
                        f"compliance_report_"
                        f"{bidder_pan_clean}_"
                        f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )

            else:

                pdf_col.warning(
                    "PDF report is temporarily unavailable."
                )

        except Exception:

            pdf_col.warning(
                "PDF report is temporarily unavailable."
            )


# ============================================================
# TAB 2 — PROTECTED AUDIT TRAIL
# ============================================================

with tab2:

    st.markdown(
        """
        <div class="section-label">Governance & traceability</div>
        <div class="section-title">Protected Verification Audit Trail</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="audit-banner">
            🔒 <b>Officer-only access.</b>
            Audit records contain verification results and officer decisions.
            This demo uses a simplified access code to demonstrate access
            control. A production deployment would use government SSO,
            role-based access control and stronger authentication.
        </div>
        """,
        unsafe_allow_html=True,
    )

    access_code = st.text_input(
        "Officer Access Code",
        type="password",
        placeholder="Enter authorized officer access code",
    )

    if access_code:

        headers = {
            "x-officer-code": access_code
        }

        try:

            resp = api_get(
                "/audit",
                headers=headers,
            )

            if resp.status_code == 401:

                st.error(
                    "❌ Incorrect officer access code."
                )

            elif resp.status_code != 200:

                st.error(
                    f"Backend error ({resp.status_code}): "
                    f"{resp.text}"
                )

            else:

                log = resp.json()

                if not log:

                    st.info(
                        "No verification records have been logged yet."
                    )

                else:

                    st.success(
                        f"🔐 Authorized access — {len(log)} "
                        f"audit record(s) available."
                    )

                    for entry in log:

                        timestamp = entry.get(
                            "timestamp",
                            "Unknown time",
                        )

                        entry_name = entry.get(
                            "bidder_name",
                            "Unknown bidder",
                        )

                        entry_score = entry.get(
                            "compliance_score",
                            "—",
                        )

                        entry_decision = entry.get(
                            "officer_decision",
                            "—",
                        )

                        with st.expander(
                            f"{timestamp}  •  "
                            f"{entry_name}  •  "
                            f"Score: {entry_score}  •  "
                            f"{entry_decision}"
                        ):

                            st.json(entry)

                            report_resp = api_get(
                                f"/audit/{entry['id']}/report",
                                headers=headers,
                            )

                            if report_resp.status_code == 200:

                                st.download_button(
                                    "📄 Download Audit PDF",
                                    data=report_resp.content,
                                    file_name=(
                                        f"compliance_report_"
                                        f"{entry.get('bidder_pan', 'record')}_"
                                        f"{entry['id']}.pdf"
                                    ),
                                    mime="application/pdf",
                                    key=f"audit_pdf_{entry['id']}",
                                )

        except requests.exceptions.ConnectionError:

            st.error(
                "⚠️ Unable to reach the backend."
            )

        except Exception as exc:

            st.error(
                f"Unexpected error: {exc}"
            )

    # --------------------------------------------------------
    # MOCK DATABASE
    # --------------------------------------------------------

    st.divider()

    with st.expander(
        "🗄️  View Mock Government Portal Database"
    ):

        st.caption(
            "Demo-only simulated records. "
            "This is not a live government database."
        )

        if not access_code:

            st.info(
                "Enter the authorized officer access code above "
                "to view the simulated portal records."
            )

        else:

            try:

                db_resp = api_get(
                    "/portal-database",
                    headers={
                        "x-officer-code": access_code
                    },
                )

                if db_resp.status_code == 200:

                    st.json(
                        db_resp.json()
                    )

                elif db_resp.status_code == 401:

                    st.error(
                        "Incorrect officer access code."
                    )

                else:

                    st.error(
                        f"Backend error ({db_resp.status_code}): "
                        f"{db_resp.text}"
                    )

            except Exception as exc:

                st.error(
                    f"Could not load mock database: {exc}"
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <br>
    <div style="
        text-align:center;
        color:#7a8792;
        font-size:0.75rem;
        padding:1.5rem 0 0.5rem 0;
        border-top:1px solid #e1e6ea;
    ">
        GeM Bid Compliance Verification Platform • SIH26100<br>
        AI-assisted decision support • Final decision remains with the
        authorized Procurement Officer
    </div>
    """,
    unsafe_allow_html=True,
)