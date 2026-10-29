import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Ensure local modules are found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from copilot_graph import run_copilot, get_provider_status, get_configured_models

app = FastAPI(title="Cynbit AI Opportunity Copilot", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLE_BRIEFS = {
    "lead_triage": {
        "title": "Inbound Lead Triage & Routing",
        "industry": "SaaS / Technology",
        "objective": "Reduce manual repetitive work",
        "constraints": "Sub-2s response SLA, existing HubSpot CRM, human review for enterprise deals > $20k.",
        "brief": """We receive 150+ inbound sales inquiries daily across our web forms and contact email.
Currently, a team of two SDRs manually reads every message, copies the prospect into HubSpot, evaluates budget and team size, and forwards the lead to the relevant account executive.
During peak hours, inquiries sit unread for up to 4 hours, and high-value leads are occasionally misrouted or delayed.
We need an automated pipeline that ingests raw inquiries, extracts company size, intent, urgency, and technical stack, normalizes the contact data, and drafts a personalized reply.
High-confidence SMB leads can receive automated confirmation emails, but any enterprise lead with budget > $20k must be flagged for human SDR approval before anything is sent."""
    },
    "invoice_ocr": {
        "title": "Invoice OCR & Multi-Vendor Reconciliation",
        "industry": "Financial Services",
        "objective": "Reduce operational cost & errors",
        "constraints": "Strict audit trail, SOC2 compliance, multi-currency support, zero tolerance for payment amount errors.",
        "brief": """Our accounts payable department processes around 3,000 vendor invoices each month from over 200 suppliers.
Invoices arrive in diverse formats: scanned paper receipts, PDF attachments, photos taken on mobile phones, and EDI feeds.
Staff manually key invoice numbers, line items, tax IDs, and totals into SAP, leading to a 3% data entry error rate and late payment penalties.
We want an AI-assisted document pipeline that automatically ingests incoming invoice PDFs/images, extracts all line-item tables with 99%+ precision, cross-checks vendor bank details against our SAP master records, and flags discrepancies.
Invoices under $1,000 matching purchase orders can be approved automatically, while exceptions and discrepancies require a 1-click human verification interface."""
    },
    "churn_forecast": {
        "title": "Customer Churn & Expansion Signals",
        "industry": "SaaS / Technology",
        "objective": "Improve decision accuracy & quality",
        "constraints": "Internal BigQuery warehouse, explainable risk factors, weekly batch inference, human CSM approval for high-risk accounts.",
        "brief": """We have 1,200 active B2B software accounts on annual contracts.
Customer Success managers are currently reactive: they only discover an account is at risk of cancellation when the renewal notice is sent 30 days prior, which is too late to salvage the relationship.
We have telemetry data in BigQuery including daily active user counts, feature adoption metrics, support ticket frequency, and CSAT scores.
We need an intelligent monitoring system that evaluates usage drops and support sentiment, identifies early churn warning signs 90 days before renewal, highlights key driver factors, and generates suggested retention interventions for the assigned CSM to review."""
    },
    "support_copilot": {
        "title": "Support Ticket Triage & Resolution Copilot",
        "industry": "E-commerce & Retail",
        "objective": "Accelerate response & turnaround time",
        "constraints": "Zendesk API integration, GDPR compliance, no automated refunds over $50 without supervisor signature.",
        "brief": """Our customer support team handles 2,500 tickets per week regarding order tracking, returns, damaged goods, and shipping delays.
Agents spend 60% of their time searching multiple internal databases (Shopify, ShipBob, Stripe) to gather context and copying canned responses.
We need an AI copilot integrated into Zendesk that automatically summarizes the customer's order history, diagnoses the root issue, checks return policy eligibility, and generates a ready-to-send draft response with specific parcel tracking links.
The agent should be able to review, edit, or approve the draft with a single keystroke."""
    }
}

class CopilotRequest(BaseModel):
    brief: str = Field(..., max_length=15000, description="Raw client notes or RFP text")
    industry: Optional[str] = "SaaS / Technology"
    objective: Optional[str] = "Reduce manual repetitive work"
    constraints: Optional[str] = ""
    provider: Optional[str] = "auto"

@app.get("/api/status")
def get_status():
    providers = get_provider_status()
    active_keys = [k for k, v in providers.items() if v]
    configured_models = get_configured_models()
    return {
        "status": "healthy",
        "providers": providers,
        "active_keys": active_keys,
        "auto_recommended": active_keys[0] if active_keys else "Deterministic Baseline",
        **configured_models
    }

@app.get("/api/samples")
def get_samples():
    return SAMPLE_BRIEFS

@app.post("/api/analyze")
def analyze_opportunity(req: CopilotRequest):
    if not req.brief or not req.brief.strip():
        raise HTTPException(status_code=400, detail="Client brief cannot be empty.")
    if len(req.brief) > 15000:
        raise HTTPException(status_code=413, detail="Client brief exceeds 15,000 character limit.")

    inputs = {
        "brief": req.brief.strip(),
        "industry": req.industry or "SaaS / Technology",
        "objective": req.objective or "Reduce manual repetitive work",
        "constraints": req.constraints or "",
        "provider": req.provider or "auto"
    }

    try:
        result = run_copilot(inputs)
        return {
            "success": True,
            "data": result,
            "inputs": inputs
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Copilot analysis failed: {str(exc)}")

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
@app.head("/")
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "Cynbit AI Copilot API is running. index.html not yet created."})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8501"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
