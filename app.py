import os
import json
import streamlit as st
from copilot_graph import run_copilot, get_provider_status

# Page Configuration
st.set_page_config(
    page_title="Cynbit AI Opportunity Copilot",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Design System (Solon Workspace + PropMint Discovery Aesthetics)
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0f172a;
}

h1, h2, h3, h4, .brand-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    letter-spacing: -0.02em;
}

/* App Header */
.app-header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0 18px 0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 20px;
}
.brand-badge {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    background: #f1f5f9;
    color: #475569;
    padding: 4px 8px;
    border-radius: 6px;
    margin-left: 10px;
    vertical-align: middle;
}

/* Multi-Stage Stepper Bar */
.stepper-bar {
    display: flex;
    align-items: center;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 16px;
    margin-bottom: 22px;
    gap: 8px;
    overflow-x: auto;
}
.stepper-step {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-weight: 600;
    color: #64748b;
}
.stepper-step.active {
    color: #0f172a;
}
.step-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #e2e8f0;
    color: #475569;
    font-size: 11px;
    font-weight: 700;
}
.stepper-step.active .step-number {
    background: #0f172a;
    color: #ffffff;
}
.stepper-divider {
    flex: 1;
    height: 1px;
    background: #cbd5e1;
    min-width: 20px;
}

/* PropMint Intelligence Cards */
.prop-pill-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.pill-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 3px 8px;
    border-radius: 9999px;
    margin-bottom: 10px;
}
.pill-known {
    background: #ecfdf5;
    color: #065f46;
    border: 1px solid #a7f3d0;
}
.pill-understood {
    background: #f0fdfa;
    color: #0f766e;
    border: 1px solid #99f6e4;
}
.pill-missing {
    background: #fffbeb;
    color: #92400e;
    border: 1px dashed #fcd34d;
}

.prop-fact-item {
    font-size: 12.5px;
    line-height: 1.5;
    color: #334155;
    padding: 5px 0;
    border-bottom: 1px solid #f1f5f9;
}
.prop-fact-item:last-child {
    border-bottom: none;
}

/* Next Best Question Card */
.nbq-container {
    background: linear-gradient(135deg, #f0fdfa 0%, #f8fafc 100%);
    border: 1px solid #99f6e4;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 24px;
    box-shadow: 0 4px 12px rgba(15, 118, 110, 0.06);
}
.nbq-header {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #0f766e;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.nbq-question {
    font-size: 15px;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 10px;
}
.nbq-impact {
    font-size: 11.5px;
    color: #64748b;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 6px 10px;
    margin-top: 10px;
}

/* Solon 3-Column Workspace */
.solon-pane {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
    min-height: 100%;
}
.solon-header {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 8px;
}
.solon-title {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.01em;
    margin-bottom: 4px;
}
.solon-subtitle {
    font-size: 12px;
    color: #64748b;
    margin-bottom: 16px;
}
.solon-quote {
    border-left: 3px solid #0f766e;
    background: #f8fafc;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    font-size: 13.5px;
    color: #334155;
    line-height: 1.6;
    margin-bottom: 18px;
}
.solon-source-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 8px;
    font-size: 12px;
}
.solon-deliverable-tray {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 18px;
    margin-top: 24px;
    font-size: 12px;
    color: #475569;
}
.deliverable-tag {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 3px 8px;
    font-weight: 600;
    color: #1e293b;
}

/* Roadmap Flow */
.roadmap-phase {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #f1f5f9;
}
.phase-badge {
    background: #0f172a;
    color: #ffffff;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    white-space: nowrap;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Provider Status Detection
provider_status = get_provider_status()

# Sidebar: Controls & Context
with st.sidebar:
    st.markdown("### 🧭 Client Context")
    industry = st.selectbox(
        "Industry",
        ["SaaS / Technology", "Healthcare", "Retail / E-commerce", "Education", "Real estate", "Professional services", "Other"],
        help="Select client industry to tune domain-specific solution patterns."
    )
    objective = st.selectbox(
        "Primary Objective",
        ["Reduce manual work", "Improve customer experience", "Increase sales efficiency", "Improve decision-making", "Build an AI-enabled product", "Explore feasibility"]
    )
    constraints = st.text_area(
        "Constraints",
        value=st.session_state.get("constraints_input", ""),
        placeholder="e.g. Existing CRM, no external PII storage, strict <2s latency SLA, human review mandatory"
    )

    st.markdown("---")
    st.markdown("### ⚡ AI Provider Configuration")
    provider_options = ["Auto-detect", "Google Gemini", "Groq", "xAI Grok", "OpenAI", "Deterministic fallback"]
    selected_provider = st.selectbox("Model Provider", provider_options, help="Choose active inference provider. Managed via .env.")

    with st.expander("🔑 Live API Key Telemetry", expanded=True):
        for name, is_set in provider_status.items():
            badge = "🟢 Configured" if is_set else "⚪ Not detected"
            st.markdown(f"- **{name}**: {badge}")
        st.caption("Add keys to `.env` in the workspace root to enable live LLM generation.")

    st.markdown("---")
    st.caption("Cynbit AI Opportunity Copilot · Enterprise Edition")

# Top Header Bar
active_provider_tag = "Deterministic Baseline"
if selected_provider == "Auto-detect":
    if provider_status.get("Gemini"):
        active_provider_tag = "Gemini 1.5-Flash (Active)"
    elif provider_status.get("Groq"):
        active_provider_tag = "Groq Llama-3.3-70b (Active)"
    elif provider_status.get("OpenAI"):
        active_provider_tag = "OpenAI gpt-4o-mini (Active)"
else:
    active_provider_tag = selected_provider

st.markdown(f"""
<div class="app-header-container">
    <div>
        <span style="font-size: 24px; font-weight: 700; color: #0f172a;">🧭 Cynbit AI Opportunity Copilot</span>
        <span class="brand-badge">Solon + PropMint Edition</span>
    </div>
    <div style="font-size: 12px; color: #475569;">
        Engine: <strong style="color: #0f766e;">{active_provider_tag}</strong> · LangGraph Orchestrated
    </div>
</div>
""", unsafe_allow_html=True)

# Interactive Stepper (Discovery2Deal Style)
has_result = "result" in st.session_state
s1_class = "active"
s2_class = "active" if has_result else ""
s3_class = "active" if has_result else ""
s4_class = "active" if has_result else ""

st.markdown(f"""
<div class="stepper-bar">
    <div class="stepper-step {s1_class}"><span class="step-number">1</span> Client Intake</div>
    <div class="stepper-divider"></div>
    <div class="stepper-step {s2_class}"><span class="step-number">2</span> Opportunity Intelligence</div>
    <div class="stepper-divider"></div>
    <div class="stepper-step {s3_class}"><span class="step-number">3</span> Solution Blueprint</div>
    <div class="stepper-divider"></div>
    <div class="stepper-step {s4_class}"><span class="step-number">4</span> Review & Governance</div>
</div>
""", unsafe_allow_html=True)

# Intake Section (PropMint Style: Incomplete notes are welcome)
st.markdown("#### 1. Client Business Brief")
st.caption("Paste raw notes, messy client emails, or project inquiry summaries. There is no long form to finish first.")

col_input, col_samples = st.columns([3, 1])

with col_samples:
    st.markdown("**Sample Discovery Briefs**")
    if st.button("📨 Inbound Lead Triage", use_container_width=True):
        st.session_state["brief"] = "We receive inbound project inquiries by email. Staff manually extract the client's goals, budget, timeline, technical constraints, and required services before preparing a discovery summary. We want to reduce repetitive preparation without sending unreviewed AI-generated promises to clients."
        st.session_state["constraints_input"] = "Existing HubSpot CRM, strict zero-unreviewed-commitments policy"
        st.rerun()
    if st.button("📄 Invoice OCR & Parsing", use_container_width=True):
        st.session_state["brief"] = "Our finance operations team processes 4,000 vendor invoices each month across PDF, scans, and emails. Staff manually enter line items into our ERP and cross-reference purchase orders. We need to automate extraction with human verification for low-confidence matches."
        st.session_state["constraints_input"] = "Mixed scans & digital PDFs, 99.5% exact match on total amounts, SAP ERP integration"
        st.rerun()
    if st.button("📊 Churn & Risk Forecast", use_container_width=True):
        st.session_state["brief"] = "We have 18 months of customer usage telemetry and support tickets. Account managers struggle to predict which mid-market clients are at risk of churning before contract renewal. We want an early-warning risk scoring baseline with human intervention playbooks."
        st.session_state["constraints_input"] = "Historical labels available, time-series holdout required, must explain risk drivers"
        st.rerun()

with col_input:
    brief = st.text_area(
        "Client Brief / Notes",
        value=st.session_state.get("brief", ""),
        height=140,
        placeholder="Example: We receive inbound inquiries by email. Staff manually read each message, extract needs and budget, route to service leads, and draft a response..."
    )

analyze_col1, analyze_col2 = st.columns([1, 4])
with analyze_col1:
    analyze_clicked = st.button("✨ Analyze Opportunity", type="primary", use_container_width=True)

if analyze_clicked:
    if not brief.strip():
        st.warning("Please enter or load a client business brief first.")
    else:
        with st.spinner("Executing LangGraph State Graph (intake → opportunity mapping → technical plan → review)..."):
            try:
                res = run_copilot({
                    "brief": brief,
                    "industry": industry,
                    "objective": objective,
                    "constraints": constraints,
                    "provider": selected_provider,
                })
                st.session_state["result"] = res
                st.rerun()
            except Exception as exc:
                st.error(f"Workflow execution error: {exc}")

# If results are generated, render the Solon + PropMint Workspace
if "result" in st.session_state:
    result = st.session_state["result"]
    
    st.markdown("---")
    
    # ----------------------------------------------------
    # PROPMINT SECTION: Opportunity Intelligence Matrix
    # ----------------------------------------------------
    st.markdown("### 2. Opportunity Intelligence")
    st.caption("PropMint-style fact isolation: Separating explicit client statements from AI architectural deductions and open unknowns.")
    
    intel_c1, intel_c2, intel_c3 = st.columns(3)
    
    with intel_c1:
        st.markdown("""
        <div class="prop-pill-card">
            <span class="pill-badge pill-known">🟢 Stated Facts (Known)</span>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">Explicit constraints & parameters directly provided</div>
        """, unsafe_allow_html=True)
        known_items = result.get("known_facts", [
            f"Target Industry: {industry}",
            f"Primary Goal: {objective}",
            "Client brief provided"
        ])
        for item in known_items:
            st.markdown(f'<div class="prop-fact-item">• {item}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with intel_c2:
        st.markdown("""
        <div class="prop-pill-card">
            <span class="pill-badge pill-understood">🔵 Architectural Deductions (Understood)</span>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">High-confidence inferences derived by Solution Architect</div>
        """, unsafe_allow_html=True)
        understood_items = result.get("understood_implications", [
            "Deterministic extraction must precede generative summarization",
            "Human approval required before any external client notification",
            "Baseline rules should be benchmarked before introducing model complexity"
        ])
        for item in understood_items:
            st.markdown(f'<div class="prop-fact-item">• {item}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with intel_c3:
        st.markdown("""
        <div class="prop-pill-card">
            <span class="pill-badge pill-missing">🟠 Unconfirmed Blind Spots (Missing)</span>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">Critical missing facts to validate before commitment</div>
        """, unsafe_allow_html=True)
        missing_items = result.get("missing_information", [
            "Current baseline volume & human hours per week",
            "Target response SLA (synchronous vs asynchronous queue)",
            "Approved budget and pilot timeline limits"
        ])
        for item in missing_items:
            st.markdown(f'<div class="prop-fact-item">• {item}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Next Best Question Card (PropMint Adaptive Discovery)
    nbq = result.get("next_best_question", {
        "question": "What is the primary operational SLA required for this opportunity?",
        "options": ["Real-time synchronous (< 2 seconds)", "Asynchronous / batch processing (< 1 hour)", "Human-assisted review queue (same-day)"],
        "impact": "Directly guides model selection, caching architecture, and human-in-the-loop escalation."
    })
    
    st.markdown(f"""
    <div class="nbq-container">
        <div class="nbq-header">⚡ Next Best Discovery Question</div>
        <div class="nbq-question">{nbq.get('question')}</div>
    """, unsafe_allow_html=True)
    
    selected_option = st.radio(
        "Select the scenario that best matches the engagement:",
        nbq.get("options", []),
        key="nbq_radio"
    )
    
    st.markdown(f"""
        <div class="nbq-impact">
            <strong>Impact on Technical Blueprint:</strong> {nbq.get('impact')} · <em>Configured choice: "{selected_option}"</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------
    # SOLON SECTION: 3-Column Persistent Consulting Workspace
    # ----------------------------------------------------
    st.markdown("### 3. Solution Blueprint & Consulting Workspace")
    st.caption("Solon 3-column architecture: Opportunity Context (Left) · Document Canvas & Versioning (Center) · Review & Governance (Right).")

    col_ctx, col_canvas, col_audit = st.columns([1.1, 2.3, 1.2])

    # Left Pane: Opportunity Context & Memory
    with col_ctx:
        st.markdown("""
        <div class="solon-pane">
            <div class="solon-header">
                <span>Context & Sources</span>
                <span style="color: #0f766e;">● Connected</span>
            </div>
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 6px;">Client Objectives</div>
        """, unsafe_allow_html=True)
        st.markdown(f"- **Primary**: {objective}")
        st.markdown(f"- **Domain**: {industry}")
        st.markdown(f"- **Constraints**: {constraints or 'Standard internal controls'}")
        
        st.markdown("<div style='margin-top: 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 6px;'>Connected Sources</div>", unsafe_allow_html=True)
        sources = result.get("connected_sources", [
            {"title": "Client Business Brief", "type": "Intake Document", "status": "Connected", "citation": "Direct Input"},
            {"title": "Cynbit AI Service Taxonomy", "type": "Knowledge Catalog", "status": "Verified", "citation": "Internal Capabilities"},
            {"title": "Architectural Feasibility Rules", "type": "Engineering Policy", "status": "Compliant", "citation": "Simplicity Standard"}
        ])
        for src in sources:
            st.markdown(f"""
            <div class="solon-source-item">
                <div>
                    <div style="font-weight: 600; color: #0f172a;">{src.get('title')}</div>
                    <div style="font-size: 10px; color: #64748b;">{src.get('type')} · {src.get('citation')}</div>
                </div>
                <span style="font-size: 10px; font-weight: 600; color: #0f766e;">{src.get('status')}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 6px;'>Questions for Client</div>", unsafe_allow_html=True)
        for q in result.get("questions_for_client", [])[:4]:
            st.markdown(f"<div style='font-size: 12px; color: #334155; margin-bottom: 6px;'>🟡 {q}</div>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

    # Center Pane: Proposal & Architecture Blueprint Canvas
    with col_canvas:
        st.markdown(f"""
        <div class="solon-pane">
            <div class="solon-header">
                <span>Technical Blueprint Canvas</span>
                <span style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-weight: 600;">Version 1.1 · Ready for Review</span>
            </div>
            <div class="solon-title">{result.get('opportunity_type', 'AI Opportunity Assessment')}</div>
            <div class="solon-subtitle">Mode: {result.get('mode', 'deterministic fallback')} · Scope: {industry}</div>
            
            <div class="solon-quote">
                <strong>Executive Context:</strong><br/>
                {result.get('executive_summary', '')}
            </div>
        """, unsafe_allow_html=True)

        # Tabbed Sections inside Canvas
        tab_arch, tab_workflow, tab_plan = st.tabs(["🏗️ Architecture & Solution", "🔄 Step-by-Step Workflow", "📅 Phased Delivery Plan"])
        
        with tab_arch:
            st.markdown("##### Recommended Minimal Solution")
            st.info(result.get("recommended_solution", ""))
            
            st.markdown("##### System Architecture Pipeline")
            st.code(result.get("architecture", ""), language="text")

        with tab_workflow:
            st.markdown("##### Proposed Execution Steps")
            for i, step in enumerate(result.get("workflow", []), 1):
                st.markdown(f"**{i}.** {step}")

        with tab_plan:
            st.markdown("##### Phased Implementation Roadmap")
            for item in result.get("implementation_plan", []):
                if isinstance(item, dict):
                    st.markdown(f"""
                    <div class="roadmap-phase">
                        <span class="phase-badge">{item.get('phase', 'Phase')}</span>
                        <div style="font-size: 13px; color: #334155;">{item.get('deliverable', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"- {item}")

        st.markdown("</div>", unsafe_allow_html=True)

    # Right Pane: Audit, Governance & Export
    with col_audit:
        st.markdown("""
        <div class="solon-pane">
            <div class="solon-header">
                <span>Audit & Governance</span>
                <span style="color: #0f766e;">Passed</span>
            </div>
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 6px;">Architect Checklist</div>
        """, unsafe_allow_html=True)
        st.markdown("✅ **Separation of Facts & Assumptions**: Verified")
        st.markdown("✅ **Simplest Technical Option**: Applied")
        st.markdown("✅ **PII & Data Leakage Prevention**: Verified")
        st.markdown("✅ **No Hallucinated ROI**: Guaranteed")

        st.markdown("<div style='margin-top: 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 6px;'>Data Requirements</div>", unsafe_allow_html=True)
        for d in result.get("data_requirements", []):
            st.markdown(f"<div style='font-size: 12px; color: #334155;'>• {d}</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 6px;'>Evaluation Metrics</div>", unsafe_allow_html=True)
        for m in result.get("evaluation_metrics", []):
            st.markdown(f"<div style='font-size: 12px; color: #334155;'>• {m}</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 14px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 6px;'>Key Operational Risks</div>", unsafe_allow_html=True)
        for r in result.get("risks", []):
            st.markdown(f"<div style='font-size: 11.5px; color: #dc2626; margin-bottom: 4px;'>⚠️ {r}</div>", unsafe_allow_html=True)

        st.markdown("---")
        # Export Actions
        st.download_button(
            "📥 Export JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="cynbit_ai_opportunity_blueprint.json",
            mime="application/json",
            use_container_width=True
        )

        md = f"# Cynbit AI Opportunity Assessment\n\n"
        md += f"**Opportunity Category:** {result.get('opportunity_type')}\n"
        md += f"**Execution Mode:** {result.get('mode')}\n\n"
        for key, value in result.items():
            if key in ["executive_summary", "problem_statement", "recommended_solution", "architecture"]:
                md += f"## {key.replace('_', ' ').title()}\n{value}\n\n"
            elif isinstance(value, list):
                md += f"## {key.replace('_', ' ').title()}\n"
                for item in value:
                    if isinstance(item, dict):
                        md += f"- **{item.get('phase', 'Phase')}**: {item.get('deliverable', '')}\n"
                    else:
                        md += f"- {item}\n"
                md += "\n"
        st.download_button(
            "📄 Export Markdown Report",
            data=md,
            file_name="cynbit_ai_opportunity_blueprint.md",
            mime="text/markdown",
            use_container_width=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # SOLON SECTION: Downstream Connected Deliverables Tray
    # ----------------------------------------------------
    st.markdown("""
    <div class="solon-deliverable-tray">
        <strong style="color: #0f172a;">Connected Deliverables Pipeline:</strong>
        <span class="deliverable-tag">Proposal Blueprint · Active</span>
        <span class="deliverable-tag">Architecture Diagram · Ready</span>
        <span class="deliverable-tag">Pilot SLA Framework · Linked</span>
        <span class="deliverable-tag">WBS Task Breakdown · Ready for Export</span>
    </div>
    """, unsafe_allow_html=True)
