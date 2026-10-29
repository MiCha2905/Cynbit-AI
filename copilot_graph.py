import json
import os
from typing import TypedDict, Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

# Load environment variables from .env
load_dotenv()

# Canonical central model configuration — Single Source of Truth
DEFAULT_MODELS = {
    "groq": "openai/gpt-oss-120b",
    "gemini": "gemini-3.8-flash",
    "openai": "gpt-4o-mini",
    "xai": "grok-2-latest",
}

def get_configured_models() -> dict[str, str]:
    """Return configured model names, ensuring server telemetry and callers use identical settings."""
    return {
        "groq_model": os.getenv("GROQ_MODEL", DEFAULT_MODELS["groq"]),
        "gemini_model": os.getenv("GEMINI_MODEL", DEFAULT_MODELS["gemini"]),
        "openai_model": os.getenv("OPENAI_MODEL", DEFAULT_MODELS["openai"]),
        "xai_model": os.getenv("XAI_MODEL", DEFAULT_MODELS["xai"]),
    }

class CopilotState(TypedDict, total=False):
    brief: str
    industry: str
    objective: str
    constraints: str
    opportunity_type: str
    analysis: dict[str, Any]
    mode: str
    provider: str
    executive_summary: str
    problem_statement: str
    recommended_solution: str
    known_facts: list[str]
    inferred_implications: list[str]
    understood_implications: list[str]  # alias for backwards compatibility
    missing_information: list[str]
    next_best_question: dict[str, Any]
    workflow: list[str]
    architecture: str
    data_requirements: list[str]
    evaluation_metrics: list[str]
    risks: list[str]
    implementation_plan: list[dict[str, str]]
    questions_for_client: list[str]
    review_checks: list[dict[str, str]]
    readiness_assessment: dict[str, Any]
    completeness_assessment: dict[str, Any]

SYSTEM_PROMPT = """You are a careful AI solution architect advising a technology services company.
Analyze the supplied client brief and propose a realistic, scoped AI opportunity.
Do not claim to know the company's internal problems. Separate explicitly stated inputs from inferences.
Prefer the simplest adequate solution; do not use an LLM if rules or conventional software are sufficient.
Do not invent ROI figures, citations, company capabilities, or data availability.
Require human review before any client-facing output.

Return valid JSON with the following exact keys:
- executive_summary: str (concise proposal summary)
- problem_statement: str (core pain point from brief)
- opportunity_type: str (e.g. Lead Triage, Document Intelligence, Predictive Analytics)
- recommended_solution: str (specific software & AI pattern)
- known_facts: array of strings ([KNOWN] explicit requirements directly stated in the client brief)
- inferred_implications: array of strings ([INFERRED] architectural deductions, workflow constraints, and assumptions derived from the brief)
- missing_information: array of strings ([MISSING] critical blind spots, unstated volumes, and unanswered questions)
- next_best_question: object with { "question": str, "options": [str, str, str], "impact": str } (the single most important clarifying question)
- workflow: array of strings (step by step technical execution steps)
- architecture: str (concise pipeline flow: Intake -> Parser -> Validation -> LLM -> Human Review -> Output)
- data_requirements: array of strings (needed ground-truth data or examples)
- evaluation_metrics: array of strings (measurable success criteria)
- risks: array of strings (operational, data, or failure risks)
- implementation_plan: array of { "phase": str, "deliverable": str } (3 to 5 phased milestones)
- questions_for_client: array of strings (questions for follow-up discovery call)
"""

REQUIRED_SCHEMA_KEYS = [
    "executive_summary",
    "problem_statement",
    "opportunity_type",
    "recommended_solution",
    "known_facts",
    "inferred_implications",
    "missing_information",
    "next_best_question",
    "workflow",
    "architecture",
    "implementation_plan",
]

def validate_proposal_schema(data: Any) -> tuple[bool, str, dict]:
    """
    Strictly validates LLM responses against expected proposal schema.
    Rejects malformed outputs, missing keys, or improper types.
    """
    if not isinstance(data, dict):
        return False, "Output must be a JSON object", {}

    for key in REQUIRED_SCHEMA_KEYS:
        if key not in data or data[key] is None:
            return False, f"Missing required key: '{key}'", {}

    # Validate non-empty string fields
    for str_key in ["executive_summary", "problem_statement", "opportunity_type", "recommended_solution", "architecture"]:
        if not isinstance(data.get(str_key), str) or not data[str_key].strip():
            return False, f"Field '{str_key}' must be a non-empty string", {}

    # Validate non-empty list fields
    for list_key in ["known_facts", "inferred_implications", "missing_information", "workflow"]:
        val = data.get(list_key)
        if not isinstance(val, list) or len(val) == 0:
            return False, f"Field '{list_key}' must be a non-empty list", {}

    # Validate next_best_question structure
    nbq = data.get("next_best_question")
    if not isinstance(nbq, dict):
        return False, "Field 'next_best_question' must be an object", {}
    if not isinstance(nbq.get("question"), str) or not nbq["question"].strip():
        return False, "Field 'next_best_question.question' must be a non-empty string", {}
    if not isinstance(nbq.get("options"), list) or len(nbq["options"]) == 0:
        return False, "Field 'next_best_question.options' must be a non-empty list", {}

    # Validate implementation_plan structure
    plan = data.get("implementation_plan")
    if not isinstance(plan, list) or len(plan) == 0:
        return False, "Field 'implementation_plan' must be a non-empty list of milestones", {}

    return True, "", data

def _baseline(state: CopilotState) -> dict:
    """Deterministic fallback; also makes the workflow runnable without an API key."""
    text = " ".join([
        state.get("brief", ""), state.get("industry", ""),
        state.get("objective", ""), state.get("constraints", "")
    ]).lower()

    if any(k in text for k in ["document", "invoice", "contract", "pdf", "form", "policy"]):
        category = "Document intelligence"
        solution = "Extract required fields from documents, validate them with deterministic rules, and route uncertain cases to a human."
        architecture = "Document parser/OCR → schema-constrained extraction → deterministic validation → human review queue."
        data = ["Representative permitted documents", "Ground-truth field labels", "Document types and exception cases"]
        metrics = ["Field-level precision/recall", "Critical-field exact-match rate", "Human correction rate", "Cost per document", "Median processing time"]
        next_q = {
            "question": "What document formats and exception rate does your current workflow handle?",
            "options": ["Native PDFs & clean digital forms (< 5% exceptions)", "Mixed scanned documents & mobile photos (10-25% exceptions)", "Unstructured free-form contracts & emails (> 30% exceptions)"],
            "impact": "Determines whether standard schema parsers or vision-language OCR pipelines are required."
        }
    elif any(k in text for k in ["lead", "sales", "prospect", "crm", "inquiry", "customer"]):
        category = "Lead and discovery workflow automation"
        solution = "Summarize inbound project inquiries, extract needs and constraints, map them to service lines, and draft follow-up questions for human approval."
        architecture = "Intake → structured extraction → service taxonomy mapping → optional LLM summary → reviewer approval."
        data = ["Synthetic or approved inquiry examples", "Service-line taxonomy", "Outcome labels if predictive routing is later desired"]
        metrics = ["Service routing macro-F1", "Requirement coverage", "Time to first draft", "Human edit rate", "Unsupported-claim rate"]
        next_q = {
            "question": "What outcome matters most after the inbound discovery triage launches?",
            "options": ["Faster response time to prospects (< 1 hour draft)", "Higher qualification accuracy & service alignment", "Strict zero-unreviewed-commitments compliance"],
            "impact": "Controls whether the system optimizes for drafting velocity, strict qualification gates, or compliance approval."
        }
    elif any(k in text for k in ["seo", "marketing", "campaign", "content", "advert"]):
        category = "Marketing performance insights"
        solution = "Summarize campaign metrics and propose evidence-linked optimization ideas for marketer review."
        architecture = "Analytics aggregation → deterministic metric checks → LLM narrative grounded in supplied metrics → approval."
        data = ["Campaign/search analytics", "Conversion definitions", "Campaign objectives and tracking caveats"]
        metrics = ["Metric correctness", "Recommendation acceptance rate", "Time to report", "Controlled-test KPI changes"]
        next_q = {
            "question": "Which advertising and analytics platforms must connect into the reporting flow?",
            "options": ["Google Analytics & Search Console only", "Meta Ads, Google Ads & CRM pipelines", "Custom internal data warehouse (BigQuery / Snowflake)"],
            "impact": "Defines integration connectors, data governance boundaries, and schema normalization layers."
        }
    elif any(k in text for k in ["review", "sentiment", "feedback", "rating"]):
        category = "Review intelligence"
        solution = "Classify review themes and sentiment, flag urgent feedback, and draft policy-aligned replies for approval."
        architecture = "Text normalization → theme/sentiment classifier → approved response policy retrieval → human review."
        data = ["Public or consented reviews", "Theme labels", "Approved response policy", "Escalation rules"]
        metrics = ["Theme macro-F1", "Urgent-review recall", "Unsupported-claim rate", "Reply approval rate"]
        next_q = {
            "question": "What is the primary policy for handling urgent or negative feedback?",
            "options": ["Immediate alert to senior team with draft response", "Automated acknowledgement with escalation ticket", "Internal classification dashboard only (no draft)"],
            "impact": "Dictates escalation webhook latency and response policy guardrails."
        }
    elif any(k in text for k in ["forecast", "predict", "churn", "demand", "risk", "anomaly"]):
        category = "Predictive analytics"
        solution = "Define a measurable prediction target, establish a simple baseline, and evaluate on a time-aware holdout before considering deployment."
        architecture = "Data audit → leakage checks → baseline model → calibration/error analysis → human decision workflow."
        data = ["Timestamped historical examples", "Reliable outcome labels", "Features available before the outcome"]
        metrics = ["PR-AUC/ROC-AUC as appropriate", "Calibration", "Recall at review capacity", "Segment-level error", "Cost of false positives/negatives"]
        next_q = {
            "question": "What historical time horizon and feature reliability does your current data have?",
            "options": ["> 12 months timestamped data with verified ground truth", "3-6 months partial data with some label noise", "Sparse data requiring heuristic baselines first"],
            "impact": "Decides whether to train supervised machine learning models or deploy statistical heuristic baselines."
        }
    else:
        category = "AI opportunity discovery"
        solution = "Turn an unstructured business request into a structured opportunity assessment with assumptions, technical options, data needs, and open questions."
        architecture = "Brief intake → opportunity taxonomy → structured analysis → validation checklist → human review."
        data = ["Business brief", "Approved service catalogue", "Constraints and success criteria", "Past proposals only if approved"]
        metrics = ["Requirement coverage", "Reviewer feasibility score", "Time to first proposal", "Unsupported-claim rate", "Stakeholder usefulness"]
        next_q = {
            "question": "What is the primary operational SLA required for this opportunity?",
            "options": ["Real-time synchronous (< 2 seconds)", "Asynchronous / batch processing (< 1 hour)", "Human-assisted review queue (same-day)"],
            "impact": "Directly guides model selection, caching architecture, and human-in-the-loop escalation."
        }

    industry = state.get("industry") or "Technology"
    obj = state.get("objective") or "Reduce manual work"
    constraints = state.get("constraints") or "No sensitive data in external APIs"

    return {
        "opportunity_type": category,
        "analysis": {
            "executive_summary": f"Potential opportunity: {category}. Treat this as an architectural hypothesis to validate with stakeholders, grounded in simplest adequate software patterns.",
            "problem_statement": state.get("brief", ""),
            "opportunity_type": category,
            "recommended_solution": solution,
            "known_facts": [
                f"[KNOWN] Target Industry: {industry}",
                f"[KNOWN] Primary Objective: {obj}",
                f"[KNOWN] Stated Constraints: {constraints}",
                "[KNOWN] Client explicitly requires human review before any client-facing commitments"
            ],
            "inferred_implications": [
                "[INFERRED] Unstructured intake must be mapped against deterministic validation rules before LLM drafting",
                "[INFERRED] Factual grounding in Cynbit's service taxonomy prevents hallucinated scope or capabilities",
                "[INFERRED] A modular pipeline allows replacing models or prompts without rewriting the workflow"
            ],
            "understood_implications": [
                "[INFERRED] Unstructured intake must be mapped against deterministic validation rules before LLM drafting",
                "[INFERRED] Factual grounding in Cynbit's service taxonomy prevents hallucinated scope or capabilities",
                "[INFERRED] A modular pipeline allows replacing models or prompts without rewriting the workflow"
            ],
            "missing_information": [
                "[MISSING] Baseline volume: Current transaction volume and human hours spent per week",
                "[MISSING] System integration endpoints: Direct API access vs manual export/import",
                "[MISSING] Acceptable error threshold: Critical fields where automation must never guess"
            ],
            "next_best_question": next_q,
            "workflow": [
                "Capture business brief, industry context, user personas, and constraints.",
                "Isolate known inputs from implied assumptions and flag missing parameters.",
                "Map request to simplest adequate technical pattern (rules, classical ML, or LLM).",
                "Define quantifiable evaluation metrics, latency targets, and operational risks.",
                "Submit structured technical proposal to human solution architect for sign-off."
            ],
            "architecture": architecture,
            "data_requirements": data,
            "evaluation_metrics": metrics,
            "risks": [
                "Unsupported assumptions or hallucinations; label assumptions explicitly and require human sign-off.",
                "Confidential data exposure; external vendor endpoints must have verified Zero Data Retention (ZDR) agreements.",
                "Overengineering; benchmark heuristics and conventional software before adding LLM components.",
                "Inference latency / cost spikes; enforce strict output token limits and caching."
            ],
            "implementation_plan": [
                {"phase": "Phase 1: Discovery", "deliverable": "Validate workflow, data permissions, volume baseline, and acceptance criteria."},
                {"phase": "Phase 2: Prototype", "deliverable": "Build structured intake, mapping heuristics, validation checks, and export."},
                {"phase": "Phase 3: Evaluation", "deliverable": "Benchmark on 20-50 synthetic briefs; measure omissions, unsupported claims, and latency."},
                {"phase": "Phase 4: Controlled Pilot", "deliverable": "Deploy assisted workflow alongside human architects with version tracking."},
                {"phase": "Phase 5: Decision Gate", "deliverable": "Promote to production only if agreed quality, latency, and business ROI thresholds are met."}
            ],
            "questions_for_client": [
                "Which workflow is most repetitive or costly, and what is its current baseline?",
                "What data can be used and what must remain in existing systems?",
                "Who approves outputs and which errors are unacceptable?",
                "Which tools or systems must the solution integrate with?",
                "What measurable result would justify a pilot?"
            ]
        },
        "mode": "Rule-based deterministic baseline (No LLM API key used)"
    }

def intake_node(state: CopilotState) -> dict:
    brief = state.get("brief", "").strip()
    if not brief:
        raise ValueError("A business brief is required.")
    if len(brief) > 15000:
        raise ValueError("Client brief exceeds maximum length of 15,000 characters.")
    # Safe bounded window (no false claims of PII sanitization)
    return {"brief": brief[:12000]}

def opportunity_mapping_node(state: CopilotState) -> dict:
    # Establish a baseline category; LLM node can refine it if configured.
    base = _baseline(state)
    return {"opportunity_type": base["opportunity_type"], "analysis": base["analysis"]}

def get_provider_status() -> dict[str, bool]:
    """Check which API keys are available in the environment."""
    return {
        "Gemini": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "Groq": bool(os.getenv("GROQ_API_KEY")),
        "xAI Grok": bool(os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")),
        "OpenAI": bool(os.getenv("OPENAI_API_KEY")),
    }

def _call_gemini(prompt: str) -> tuple[dict, str]:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set.")
    model = get_configured_models()["gemini_model"]

    # Try official google-genai SDK first
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model,
            contents=f"System Instructions:\n{SYSTEM_PROMPT}\n\nUser Request:\n{prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )
        return json.loads(response.text), f"LLM-assisted (Gemini: {model})"
    except Exception:
        # Fallback to direct REST API
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        payload = {
            "contents": [{"parts": [{"text": f"System Instructions:\n{SYSTEM_PROMPT}\n\nUser Request:\n{prompt}"}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
        }
        res = requests.post(url, json=payload, timeout=25)
        res.raise_for_status()
        data = res.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text), f"LLM-assisted (Gemini: {model})"

def _call_groq(prompt: str) -> tuple[dict, str]:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY is not set.")
    model = get_configured_models()["groq_model"]
    from groq import Groq
    client = Groq(api_key=key.strip())
    
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content), f"LLM-assisted (Groq: {model})"
    except Exception:
        # Fallback to 20B if 120B is rate-limited or busy
        fallback_model = "openai/gpt-oss-20b"
        response = client.chat.completions.create(
            model=fallback_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response.choices[0].message.content), f"LLM-assisted (Groq: {fallback_model})"

def _call_xai(prompt: str) -> tuple[dict, str]:
    key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    if not key:
        raise ValueError("XAI_API_KEY is not set.")
    model = get_configured_models()["xai_model"]
    from openai import OpenAI
    client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    return json.loads(response.choices[0].message.content), f"LLM-assisted (xAI Grok: {model})"

def _call_openai(prompt: str) -> tuple[dict, str]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY is not set.")
    model = get_configured_models()["openai_model"]
    from openai import OpenAI
    client = OpenAI(api_key=key)
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    return json.loads(response.choices[0].message.content), f"LLM-assisted (OpenAI: {model})"

def technical_plan_node(state: CopilotState) -> dict:
    selected_provider = (state.get("provider") or "auto").lower()

    prompt = (
        f"Industry: {state.get('industry','')}\n"
        f"Objective: {state.get('objective','')}\n"
        f"Constraints: {state.get('constraints','')}\n"
        f"Client brief:\n{state.get('brief','')}\n\n"
        "Create a JSON object following the system schema. Do not invent facts or ROI."
    )

    status = get_provider_status()

    # Determine provider target
    target = None
    if "gemini" in selected_provider:
        target = "gemini"
    elif "groq" in selected_provider and "grok" not in selected_provider:
        target = "groq"
    elif "grok" in selected_provider or "xai" in selected_provider:
        target = "xai"
    elif "openai" in selected_provider:
        target = "openai"
    elif selected_provider in ["deterministic", "baseline"]:
        return {"mode": "deterministic fallback"}
    elif selected_provider in ["auto", ""]:
        # Auto-detection: prioritize active working keys
        if status.get("Groq"):
            target = "groq"
        elif status.get("Gemini"):
            target = "gemini"
        elif status.get("xAI Grok"):
            target = "xai"
        elif status.get("OpenAI"):
            target = "openai"
        else:
            return {"mode": "deterministic fallback (no API keys detected in .env)"}
    else:
        # Explicit unrecognized provider requested
        return {"mode": f"deterministic fallback (unrecognized provider '{selected_provider}')"}

    try:
        if target == "groq":
            parsed, mode_str = _call_groq(prompt)
        elif target == "gemini":
            try:
                parsed, mode_str = _call_gemini(prompt)
            except Exception as gemini_err:
                if status.get("Groq"):
                    parsed, mode_str = _call_groq(prompt)
                else:
                    raise gemini_err
        elif target == "xai":
            parsed, mode_str = _call_xai(prompt)
        elif target == "openai":
            parsed, mode_str = _call_openai(prompt)
        else:
            return {"mode": "deterministic fallback"}

        # Strict response-schema validation
        is_valid, validation_err, validated_data = validate_proposal_schema(parsed)
        if not is_valid:
            # Reject malformed model output and fall back cleanly
            return {
                "mode": f"deterministic fallback (model output rejected: {validation_err})"
            }

        return {"analysis": validated_data, "mode": mode_str}
    except Exception as exc:
        # Fall back safely with clean diagnostic message
        err_msg = f"{type(exc).__name__}: {str(exc)[:100]}"
        return {"mode": f"deterministic fallback ({target.title()} error: {err_msg})"}

def compute_review_checks(analysis: dict, brief: str = "", constraints: str = "") -> list[dict]:
    """
    Audits the generated proposal across 3 dimensions using evidence-based statuses:
    - PASS: Explicit deterministic criteria met
    - REVIEW: Unresolved technical, regulatory, or policy dependencies requiring architect sign-off
    - NOT ASSESSED: Insufficient quantitative or ground-truth data in brief to evaluate
    """
    workflow = analysis.get("workflow", [])
    arch = (analysis.get("architecture") or "").lower()
    combined_text = f"{brief} {constraints}".lower()

    # 1. Technical Feasibility Audit
    # Checks whether both deterministic pre-validation AND human review escalation exist
    has_validation = any(k in arch or any(k in s.lower() for s in workflow) for k in ["validation", "rule", "schema", "parser", "ocr"])
    has_human_gate = any("human" in s.lower() or "review" in s.lower() or "approval" in s.lower() for s in workflow) or "human" in arch

    if has_validation and has_human_gate:
        tech_verdict = "PASS"
        tech_notes = "Gated. Concrete deterministic validation and human escalation checkpoints are specified in the workflow."
    elif has_validation or has_human_gate:
        tech_verdict = "REVIEW"
        tech_notes = "Needs Review. Architecture includes either validation or human review, but both are required for autonomous production readiness."
    else:
        tech_verdict = "REVIEW"
        tech_notes = "Needs Review. Workflow lacks explicit deterministic pre-validation or human review gates. Feasibility cannot be verified without pipeline schematics."

    # 2. Security & Data Risks Audit
    has_compliance_keywords = any(k in combined_text for k in ["pii", "hipaa", "gdpr", "soc2", "bank", "financial", "confidential", "secret"])
    if has_compliance_keywords:
        sec_verdict = "REVIEW"
        sec_notes = "Compliance Gap Flagged. Client brief mentions regulated or sensitive data. An isolated tenant, zero-logging enterprise agreement (ZDR), or on-premise model is required."
    else:
        sec_verdict = "REVIEW"
        sec_notes = "Vendor Policy Review Required. External LLM calls transmit brief content. Zero Data Retention (ZDR) agreements and residency policies must be verified before production."

    # 3. Business Value & Scope Audit
    has_numbers = any(char.isdigit() for char in brief)
    has_metrics = any(k in combined_text for k in ["$", "hours", "%", "daily", "monthly", "cost", "inquiries", "invoices", "tickets", "accounts"])

    if has_numbers and has_metrics:
        val_verdict = "REVIEW"
        val_notes = "Hypothesis. Target pain point has initial volume/cost metrics, but formal ROI calculation requires client baseline validation."
    else:
        val_verdict = "NOT ASSESSED"
        val_notes = "Not Assessed. Client brief lacks baseline transaction volume or labor cost data needed to substantiate economic payoff."

    return [
        {
            "id": "technical_feasibility",
            "name": "Technical Feasibility",
            "icon": "🛠️",
            "verdict": tech_verdict,
            "notes": tech_notes
        },
        {
            "id": "security_data_risks",
            "name": "Security & Data Risks",
            "icon": "🔒",
            "verdict": sec_verdict,
            "notes": sec_notes
        },
        {
            "id": "business_value",
            "name": "Business Value & Scope",
            "icon": "💰",
            "verdict": val_verdict,
            "notes": val_notes
        }
    ]

def compute_completeness_assessment(analysis: dict) -> dict:
    """
    Structural completeness score (0-100) based on coverage of proposal components:
    1. Requirements coverage (max 25 pts)
    2. Architecture completeness (max 25 pts)
    3. Blind spot isolation (max 25 pts)
    4. Operational risk cataloging (max 25 pts)

    NOTE: This measures structural proposal completeness.
    It does not certify technical feasibility or factual correctness.
    """
    known = analysis.get("known_facts") or []
    missing = analysis.get("missing_information") or []
    arch = analysis.get("architecture") or ""
    plan = analysis.get("implementation_plan") or []
    risks = analysis.get("risks") or []
    next_q = analysis.get("next_best_question") or {}

    checks = []
    total_score = 0

    # 1. Requirements Coverage
    req_pass = len(known) >= 2 and bool(analysis.get("problem_statement"))
    req_score = 25 if req_pass else (15 if len(known) >= 1 else 5)
    total_score += req_score
    checks.append({
        "name": "Requirements Coverage",
        "passed": req_pass,
        "score": req_score,
        "max": 25,
        "detail": f"{len(known)} stated constraints and requirements isolated from brief."
    })

    # 2. Architecture Completeness
    arch_pass = bool(arch) and len(plan) >= 3
    arch_score = 25 if arch_pass else (15 if bool(arch) else 5)
    total_score += arch_score
    checks.append({
        "name": "Architecture & Phasing",
        "passed": arch_pass,
        "score": arch_score,
        "max": 25,
        "detail": f"Target pipeline defined with {len(plan)} phased delivery milestones."
    })

    # 3. Blind Spots & Next-Best Question
    gaps_pass = len(missing) >= 1 and bool(next_q.get("question"))
    gaps_score = 25 if gaps_pass else (15 if len(missing) >= 1 else 5)
    total_score += gaps_score
    checks.append({
        "name": "Blind Spot Isolation",
        "passed": gaps_pass,
        "score": gaps_score,
        "max": 25,
        "detail": f"{len(missing)} open questions identified; clarifying question prioritized."
    })

    # 4. Operational Risk Cataloging
    risk_pass = len(risks) >= 2
    risk_score = 25 if risk_pass else (15 if len(risks) >= 1 else 5)
    total_score += risk_score
    checks.append({
        "name": "Risk & Governance",
        "passed": risk_pass,
        "score": risk_score,
        "max": 25,
        "detail": f"{len(risks)} operational risks mapped with human review gate."
    })

    status = "Draft Structurally Complete" if total_score >= 80 else "Incomplete Discovery Scope"

    return {
        "score": total_score,
        "status": status,
        "checks": checks,
        "disclaimer": "Measures structural completeness of proposal components. Does not guarantee technical feasibility or factual accuracy."
    }

# Backward compatibility alias
compute_readiness_assessment = compute_completeness_assessment

def review_node(state: CopilotState) -> dict:
    a = state.get("analysis") or {}
    # Ensure expected keys exist, even if the model omits one.
    defaults = _baseline(state)["analysis"]
    merged = {**defaults, **a}

    # Normalize inferred_implications and understood_implications
    if "inferred_implications" not in merged or not merged["inferred_implications"]:
        merged["inferred_implications"] = merged.get("understood_implications", [])
    merged["understood_implications"] = merged["inferred_implications"]

    brief = state.get("brief", "")
    constraints = state.get("constraints", "")

    # Compute evidence-based review checks and completeness assessment
    merged["review_checks"] = compute_review_checks(merged, brief, constraints)
    merged["completeness_assessment"] = compute_completeness_assessment(merged)
    merged["readiness_assessment"] = merged["completeness_assessment"]

    return {"analysis": merged}

builder = StateGraph(CopilotState)
builder.add_node("intake", intake_node)
builder.add_node("opportunity_mapping", opportunity_mapping_node)
builder.add_node("technical_plan", technical_plan_node)
builder.add_node("review", review_node)
builder.add_edge(START, "intake")
builder.add_edge("intake", "opportunity_mapping")
builder.add_edge("opportunity_mapping", "technical_plan")
builder.add_edge("technical_plan", "review")
builder.add_edge("review", END)
graph = builder.compile()

def run_copilot(inputs: dict) -> dict:
    state = graph.invoke(inputs)
    result = dict(state.get("analysis", {}))
    result["mode"] = state.get("mode", "unknown")
    return result
