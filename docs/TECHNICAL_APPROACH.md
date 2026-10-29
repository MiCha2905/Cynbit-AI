# Technical Approach Report — LangGraph Copilot

## 1. Objective
Convert a client business brief into a structured, reviewable AI opportunity assessment. The prototype is decision support; it must not send proposals or make commitments autonomously.

## 2. Why LangGraph?
LangGraph is used to orchestrate explicit steps with shared state. This is useful because the task is naturally decomposed into intake, opportunity mapping, technical planning, and review. The graph is linear in this version but can later support conditional routing, clarification loops, retries, and human approval gates.

## 3. Architecture
- UI: Streamlit.
- Orchestration: LangGraph `StateGraph` with typed state.
- Baseline: transparent keyword/rule mapping.
- Optional language model: hosted chat-completion API with JSON output.
- Review node: merges model output with defaults to ensure required fields exist.
- Output: JSON and Markdown downloads.

## 4. Graph nodes
1. `intake`: checks that a brief exists and limits its length.
2. `opportunity_mapping`: establishes a baseline category and solution using rules.
3. `technical_plan`: calls an LLM only when an API key is configured; otherwise continues in deterministic mode.
4. `review`: fills missing output fields with safe defaults and returns a consistent report.

Current graph:
`START → intake → opportunity_mapping → technical_plan → review → END`

Future conditional branches could route document use cases to extraction, CRM tasks to lead triage, prediction requests through a data-readiness gate, and vague briefs to a clarification node.

## 5. Model selection
Do not fine-tune initially: no approved, labeled internal dataset is available. Use a deterministic baseline first. An optional low-temperature LLM can improve synthesis for language-heavy tasks, but its outputs must be evaluated. If factual grounding in Cynbit's service catalogue becomes important, add RAG over approved sources with source metadata and citations. For simple classification, compare the LLM against rules or a small supervised classifier.

## 6. Prompt design
The system prompt instructs the model to:
- Act as a careful solution architect.
- Separate input facts from assumptions.
- Prefer the simplest adequate technical approach.
- Avoid invented ROI, citations, capabilities, or data availability.
- Return a fixed JSON schema.
- Keep a human reviewer in control.

Production hardening should add a JSON Schema/Pydantic validation layer, output length limits, retry/fallback policies, prompt-injection handling, and a test suite for malformed or unsupported output.

## 7. Data pipeline
1. Collect only brief, industry, objective, and constraints.
2. Minimize/redact sensitive data.
3. Route through the baseline taxonomy.
4. Optionally generate a structured plan using the LLM.
5. Merge with defaults and validate expected fields.
6. Display output and require human review.
7. Export JSON or Markdown.

A future RAG pipeline should ingest only approved company pages, service descriptions, case studies, and proposal templates; chunk by section; preserve title, URL, and timestamp; retrieve relevant passages; and require source-grounded statements about Cynbit.

## 8. Evaluation
Prepare 20–50 synthetic or anonymized briefs, including vague, conflicting, out-of-scope, and data-poor examples. Score outputs (0–2 each) for:
- Requirement coverage.
- Technical feasibility.
- Fact/assumption separation.
- Risk/privacy awareness.
- Actionability.

Track unsupported claims, critical omissions, reviewer edit rate, time to acceptable draft, latency, and cost. Compare deterministic and LLM modes on a held-out set. Do not claim performance gains before measurement.

## 9. Security
Never commit API keys. Use environment variables or a managed secret store. Do not submit confidential client data to a model provider without approval. Production requires authentication, access controls, retention rules, logging, and human approval for client-facing content.

## 10. Execution plan
- Week 1: stakeholder interviews, process map, baseline, data/security review.
- Weeks 2–3: prototype and test cases.
- Week 4: offline evaluation and error analysis.
- Weeks 5–6: limited human-reviewed pilot.
- Decision gate: expand only after agreed quality, security, and business thresholds are met.

## 11. Limitations
The baseline is rules-based, not a trained ML model. Optional LLM output can be incorrect. No internal Cynbit operational data was available, so business pain points and expected benefits remain hypotheses. No CRM integration or production deployment is included.
