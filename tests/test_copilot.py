import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from copilot_graph import (
    run_copilot,
    compute_completeness_assessment,
    compute_readiness_assessment,
    compute_review_checks,
    validate_proposal_schema,
    get_configured_models
)
from server import app

client = TestClient(app)

def test_deterministic_baseline_execution():
    """Verify deterministic fallback produces structured output without API keys."""
    inputs = {
        "brief": "We receive 150+ inbound customer inquiries daily by email. Need automated triage under 2s with human review for deals > $20k.",
        "industry": "SaaS / Technology",
        "objective": "Reduce manual repetitive work",
        "constraints": "Sub-2s response SLA, human review mandatory",
        "provider": "deterministic"
    }
    result = run_copilot(inputs)
    assert result is not None
    assert "mode" in result
    assert "deterministic" in result["mode"].lower()

def test_fact_classification_triad():
    """Verify the 3-tier fact classification [KNOWN], [INFERRED], and [MISSING] exist."""
    inputs = {
        "brief": "Inbound invoice parsing and vendor reconciliation for accounts payable.",
        "industry": "Financial Services",
        "objective": "Reduce operational cost & errors",
        "provider": "deterministic"
    }
    result = run_copilot(inputs)

    # 1. Known facts (Stated in brief / input)
    known = result.get("known_facts", [])
    assert isinstance(known, list)
    assert len(known) >= 1

    # 2. Inferred implications (Deductions / assumptions)
    inferred = result.get("inferred_implications", [])
    assert isinstance(inferred, list)
    assert len(inferred) >= 1

    # 3. Missing information (Blind spots / unanswered questions)
    missing = result.get("missing_information", [])
    assert isinstance(missing, list)
    assert len(missing) >= 1

def test_next_best_question_contract():
    """Verify next_best_question has question, options, and impact for interactive selection."""
    inputs = {
        "brief": "Customer churn prediction using BigQuery telemetry metrics.",
        "industry": "SaaS / Technology",
        "objective": "Improve decision accuracy & quality",
        "provider": "deterministic"
    }
    result = run_copilot(inputs)
    nbq = result.get("next_best_question", {})
    assert "question" in nbq
    assert isinstance(nbq["question"], str) and len(nbq["question"]) > 5
    assert "options" in nbq
    assert isinstance(nbq["options"], list) and len(nbq["options"]) >= 2
    assert "impact" in nbq
    assert isinstance(nbq["impact"], str) and len(nbq["impact"]) > 0

def test_completeness_assessment_logic():
    """Verify completeness score is calculated transparently from structural checks."""
    sample_analysis = {
        "problem_statement": "Automate lead routing.",
        "known_facts": ["Industry: SaaS", "Latency: <2s"],
        "architecture": "Webhook -> Parser -> Rule Gate -> Human Review Queue",
        "implementation_plan": [
            {"phase": "Phase 1", "deliverable": "Discovery & Prototype"},
            {"phase": "Phase 2", "deliverable": "Pilot with Review Queue"},
            {"phase": "Phase 3", "deliverable": "Production Rollout"}
        ],
        "missing_information": ["Daily email volume", "HubSpot credential endpoints"],
        "next_best_question": {"question": "What is daily volume?", "options": ["High", "Low"], "impact": "Infrastructure"},
        "risks": ["Misrouting high-value deals", "API rate limits"]
    }
    assessment = compute_completeness_assessment(sample_analysis)
    assert "score" in assessment
    assert 0 <= assessment["score"] <= 100
    assert "checks" in assessment
    assert len(assessment["checks"]) == 4
    assert "disclaimer" in assessment

    # Verify each check has transparent scoring criteria
    for chk in assessment["checks"]:
        assert "name" in chk
        assert "passed" in chk
        assert "score" in chk
        assert "max" in chk
        assert "detail" in chk

def test_evidence_based_review_verdicts():
    """Verify review council returns dynamic statuses (PASS, REVIEW, NOT ASSESSED) based on brief evidence."""
    # Scenario A: Inbound inquiry with validation, human gate, and quantitative metrics
    analysis_a = {
        "workflow": ["Ingest email", "Deterministic validation against schema rules", "Human review queue for approval"],
        "architecture": "Parser -> Schema validation -> Human review queue",
        "problem_statement": "Reduce manual entry"
    }
    checks_a = compute_review_checks(analysis_a, brief="We process 150 inquiries daily costing 4 hours", constraints="Human review mandatory")
    tech_a = next(c for c in checks_a if c["id"] == "technical_feasibility")
    val_a = next(c for c in checks_a if c["id"] == "business_value")
    sec_a = next(c for c in checks_a if c["id"] == "security_data_risks")

    assert tech_a["verdict"] == "PASS"
    assert val_a["verdict"] == "REVIEW"  # Has quantitative numbers, but needs client baseline verification
    assert sec_a["verdict"] == "REVIEW"

    # Scenario B: Vague brief without quantitative numbers and without validation
    analysis_b = {
        "workflow": ["Call LLM directly", "Send output to customer"],
        "architecture": "Intake -> LLM -> Output",
        "problem_statement": "Make things faster"
    }
    checks_b = compute_review_checks(analysis_b, brief="We want AI for our business", constraints="")
    tech_b = next(c for c in checks_b if c["id"] == "technical_feasibility")
    val_b = next(c for c in checks_b if c["id"] == "business_value")

    assert tech_b["verdict"] == "REVIEW"
    assert val_b["verdict"] == "NOT ASSESSED"  # No numbers or metrics in brief

def test_schema_validation_accepts_valid_payload():
    """Verify validate_proposal_schema accepts conforming dictionary."""
    valid_payload = {
        "executive_summary": "Valid summary",
        "problem_statement": "Valid problem",
        "opportunity_type": "Lead Triage",
        "recommended_solution": "Rule parser and queue",
        "known_facts": ["[KNOWN] Item 1"],
        "inferred_implications": ["[INFERRED] Item 2"],
        "missing_information": ["[MISSING] Item 3"],
        "next_best_question": {"question": "Volume?", "options": ["A", "B"], "impact": "Scale"},
        "workflow": ["Step 1", "Step 2"],
        "architecture": "Intake -> Filter -> Output",
        "implementation_plan": [{"phase": "Phase 1", "deliverable": "Design"}]
    }
    is_valid, err, data = validate_proposal_schema(valid_payload)
    assert is_valid is True
    assert err == ""
    assert data == valid_payload

def test_schema_validation_rejects_malformed_model_output():
    """Verify validate_proposal_schema rejects incomplete or type-mismatched output."""
    # Missing required key
    invalid_1 = {"executive_summary": "Only summary"}
    is_valid_1, err_1, _ = validate_proposal_schema(invalid_1)
    assert is_valid_1 is False
    assert "Missing required key" in err_1

    # Empty list for workflow
    invalid_2 = {
        "executive_summary": "Summary",
        "problem_statement": "Problem",
        "opportunity_type": "Type",
        "recommended_solution": "Solution",
        "known_facts": ["Fact 1"],
        "inferred_implications": ["Inference 1"],
        "missing_information": ["Missing 1"],
        "next_best_question": {"question": "Q?", "options": ["Opt 1"]},
        "workflow": [],  # Empty!
        "architecture": "Architecture",
        "implementation_plan": [{"phase": "P1", "deliverable": "D1"}]
    }
    is_valid_2, err_2, _ = validate_proposal_schema(invalid_2)
    assert is_valid_2 is False
    assert "Field 'workflow' must be a non-empty list" in err_2

def test_provider_failure_graceful_fallback():
    """Verify that an unavailable or failing LLM provider gracefully falls back to deterministic rules."""
    inputs = {
        "brief": "Inbound inquiry triage across multiple regions.",
        "industry": "SaaS",
        "objective": "Automation",
        "constraints": "Sub-2s SLA",
        "provider": "non_existent_provider_xyz"
    }
    result = run_copilot(inputs)
    assert result is not None
    assert "mode" in result
    assert "deterministic" in result["mode"].lower()

def test_provider_exception_triggers_fallback(monkeypatch):
    """Verify that a runtime network or API error during LLM generation triggers clean fallback."""
    import copilot_graph
    def mock_failing_groq(prompt):
        raise ConnectionError("Simulated Groq 503 Service Unavailable")
    monkeypatch.setattr(copilot_graph, "_call_groq", mock_failing_groq)

    inputs = {
        "brief": "Inbound inquiry triage across multiple regions.",
        "provider": "groq"
    }
    result = copilot_graph.run_copilot(inputs)
    assert result is not None
    assert "deterministic fallback" in result["mode"].lower()
    assert "ConnectionError" in result["mode"]

def test_api_status_endpoint():
    """Verify /api/status returns unified model telemetry matching copilot_graph."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "providers" in data
    
    # Check that model telemetry keys exist and match get_configured_models()
    models = get_configured_models()
    assert data["groq_model"] == models["groq_model"]
    assert data["gemini_model"] == models["gemini_model"]

def test_api_analyze_endpoint():
    """Verify /api/analyze accepts inputs and returns valid blueprint."""
    payload = {
        "brief": "Inbound inquiry parsing with sub-2s latency and human review for high-value leads.",
        "industry": "SaaS / Technology",
        "objective": "Reduce manual repetitive work",
        "constraints": "Sub-2s response SLA, human review mandatory",
        "provider": "deterministic"
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "recommended_solution" in data["data"]
    assert "architecture" in data["data"]

def test_api_analyze_empty_brief_validation():
    """Verify /api/analyze rejects empty brief."""
    response = client.post("/api/analyze", json={"brief": "   "})
    assert response.status_code == 400

def test_api_analyze_request_size_limit():
    """Verify /api/analyze rejects oversized briefs (>15,000 chars) for request bounding."""
    oversized_brief = "A" * 15001
    response = client.post("/api/analyze", json={"brief": oversized_brief})
    assert response.status_code in [400, 413, 422]
