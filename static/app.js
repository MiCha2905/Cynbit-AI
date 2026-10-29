// ==========================================================================
// Cynbit AI Opportunity Copilot — Editorial SaaS Workspace Controller
// ==========================================================================

let latestProposal = null;
let selectedOptionText = null;

const SAMPLE_BRIEF = {
  brief: `We receive 150+ inbound sales inquiries daily by email. Staff manually read each message, copy into HubSpot, evaluate budget, and forward to AEs. Inquiries sit unread for 4 hours. We need an automated extraction pipeline with sub-2s SLA and strict human review for enterprise leads > $20k.`,
  industry: "SaaS / Technology",
  objective: "Reduce manual repetitive work",
  constraints: "Sub-2s response SLA, human review for enterprise deals > $20k"
};

document.addEventListener('DOMContentLoaded', () => {
  setupApp();
});

async function setupApp() {
  bindEvents();
  await checkStatus();
  // Auto-load sample so user immediately sees an active proposal
  loadSampleBrief(true);
}

// --------------------------------------------------------------------------
// 1. Engine Telemetry & Mode
// --------------------------------------------------------------------------
async function checkStatus() {
  const dot = document.getElementById('status-dot');
  const statusText = document.getElementById('engine-status-text');
  const modeLabel = document.getElementById('doc-mode-label');

  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    const activeKeys = data.active_keys || [];

    if (activeKeys.includes('Groq')) {
      dot.className = 'status-dot active-groq';
      const model = data.groq_model || 'openai/gpt-oss-120b';
      statusText.textContent = `Live: Groq (${model})`;
      if (modeLabel) modeLabel.textContent = `Orchestrated with LangGraph · Groq`;
    } else if (activeKeys.includes('Gemini')) {
      dot.className = 'status-dot active-gemini';
      const model = data.gemini_model || 'gemini-3.8-flash';
      statusText.textContent = `Live: Gemini (${model})`;
      if (modeLabel) modeLabel.textContent = `Orchestrated with LangGraph · Gemini`;
    } else {
      dot.className = 'status-dot active-baseline';
      statusText.textContent = 'Mode: Rule-Based Baseline';
      if (modeLabel) modeLabel.textContent = 'Orchestrated with LangGraph · Deterministic';
    }
  } catch (e) {
    dot.className = 'status-dot active-baseline';
    statusText.textContent = 'Mode: Deterministic Baseline';
    if (modeLabel) modeLabel.textContent = 'Deterministic Baseline';
  }
}

// --------------------------------------------------------------------------
// 2. Event Binding
// --------------------------------------------------------------------------
function bindEvents() {
  const briefEl = document.getElementById('input-brief');
  briefEl.addEventListener('input', () => {
    document.getElementById('brief-char-count').textContent = `${briefEl.value.length} characters`;
  });

  document.getElementById('btn-load-sample').addEventListener('click', () => {
    loadSampleBrief(false);
  });

  document.getElementById('btn-analyze').addEventListener('click', () => {
    analyzeOpportunity();
  });

  document.getElementById('btn-apply-answer').addEventListener('click', () => {
    applyClarifyingAnswer();
  });

  document.getElementById('btn-copy-proposal').addEventListener('click', copyProposal);
  document.getElementById('btn-export-md').addEventListener('click', exportMarkdown);
  document.getElementById('btn-download-json').addEventListener('click', exportJson);

  const scrollTopBtn = document.getElementById('btn-scroll-top');
  if (scrollTopBtn) {
    scrollTopBtn.addEventListener('click', () => {
      document.querySelector('.canvas-main').scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
}

function loadSampleBrief(autoRun = false) {
  document.getElementById('input-brief').value = SAMPLE_BRIEF.brief;
  document.getElementById('select-industry').value = SAMPLE_BRIEF.industry;
  document.getElementById('select-objective').value = SAMPLE_BRIEF.objective;
  document.getElementById('input-constraints').value = SAMPLE_BRIEF.constraints;
  document.getElementById('brief-char-count').textContent = `${SAMPLE_BRIEF.brief.length} characters`;

  if (autoRun) {
    analyzeOpportunity();
  } else {
    showToast('Loaded sample lead triage brief.');
  }
}

// --------------------------------------------------------------------------
// 3. LangGraph Execution
// --------------------------------------------------------------------------
async function analyzeOpportunity() {
  const brief = document.getElementById('input-brief').value.trim();
  if (!brief) {
    showToast('Please enter client notes or click "Load sample".');
    return;
  }

  const industry = document.getElementById('select-industry').value;
  const objective = document.getElementById('select-objective').value;
  const constraints = document.getElementById('input-constraints').value;
  const provider = document.getElementById('select-provider').value;

  const btn = document.getElementById('btn-analyze');
  const spinner = document.getElementById('analyze-spinner');
  const btnText = document.getElementById('analyze-btn-text');

  btn.disabled = true;
  spinner.classList.remove('hidden');
  btnText.textContent = 'Developing Proposal...';

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brief, industry, objective, constraints, provider })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Analysis request failed.');
    }

    const payload = await res.json();
    latestProposal = payload.data;
    renderProposal(payload.data, payload.inputs);
    showToast('Solution proposal generated.');
  } catch (err) {
    console.error(err);
    showToast(`Error: ${err.message}`);
  } finally {
    btn.disabled = false;
    spinner.classList.add('hidden');
    btnText.textContent = 'Generate Proposal';
  }
}

// --------------------------------------------------------------------------
// 4. Render Proposal Canvas
// --------------------------------------------------------------------------
function renderProposal(data, inputs) {
  // Breadcrumbs & Title
  const category = data.opportunity_type || 'Routing & Assignment Optimization';
  const navCat = document.getElementById('nav-category');
  if (navCat) navCat.textContent = category;

  const titleEl = document.getElementById('disp-title');
  if (titleEl) titleEl.textContent = category;

  // Header meta & lead
  const modeLabel = document.getElementById('doc-mode-label');
  if (modeLabel && data.mode) {
    modeLabel.textContent = `LangGraph · ${data.mode}`;
  }

  const summaryEl = document.getElementById('disp-exec-summary');
  if (summaryEl) summaryEl.textContent = data.executive_summary || '';

  // 01 — Current Situation & Problem
  const problemEl = document.getElementById('disp-problem');
  if (problemEl) {
    problemEl.textContent = data.problem_statement || 'Evaluating client context and operational hurdles...';
  }

  // 02 — Fact & Gap Analysis (Known, Inferred, Missing)
  renderFactClassification(data);

  // 03 — Next-Best Question
  renderNextBestQuestion(data);

  // 04 — Approach & Target Architecture
  const solutionEl = document.getElementById('disp-solution');
  if (solutionEl) solutionEl.textContent = data.recommended_solution || '';

  const archEl = document.getElementById('disp-architecture');
  if (archEl) archEl.textContent = data.architecture || '';

  const wfList = document.getElementById('disp-workflow');
  if (wfList) {
    const workflow = data.workflow || [];
    wfList.innerHTML = workflow.length
      ? workflow.map(w => `<li>${escapeHtml(w)}</li>`).join('')
      : '<li>Workflow steps will be generated upon analysis.</li>';
  }

  // 05 — Phased Implementation & Success Criteria
  const phasesBox = document.getElementById('disp-phases');
  if (phasesBox) {
    const plan = data.implementation_plan || [];
    phasesBox.innerHTML = plan.map(p => `
      <div class="editorial-phase-row">
        <span class="phase-name">${escapeHtml(p.phase || 'Phase')}</span>
        <span class="phase-deliverable">${escapeHtml(p.deliverable || '')}</span>
      </div>
    `).join('');
  }

  const metricsList = document.getElementById('disp-metrics');
  if (metricsList) {
    const metrics = data.evaluation_metrics || [];
    metricsList.innerHTML = metrics.map(m => `<li>${escapeHtml(m)}</li>`).join('');
  }

  const dataList = document.getElementById('disp-data');
  if (dataList) {
    const dataReqs = data.data_requirements || [];
    dataList.innerHTML = dataReqs.map(d => `<li>${escapeHtml(d)}</li>`).join('');
  }

  // 06 — Governance, Risks & Review Council
  renderReviewAndReadiness(data);
}

// --------------------------------------------------------------------------
// Fact Classification ([KNOWN], [INFERRED], [MISSING])
// --------------------------------------------------------------------------
function renderFactClassification(data) {
  const known = data.known_facts || [];
  const inferred = data.inferred_implications || data.understood_implications || [];
  const missing = data.missing_information || [];

  const knownList = document.getElementById('list-known');
  if (knownList) {
    knownList.innerHTML = known.length
      ? known.map(cleanFactTag).map(f => `<li>${escapeHtml(f)}</li>`).join('')
      : '<li style="font-style:italic;color:var(--text-tertiary)">No stated items isolated.</li>';
  }

  const inferredList = document.getElementById('list-inferred');
  if (inferredList) {
    inferredList.innerHTML = inferred.length
      ? inferred.map(cleanFactTag).map(i => `<li>${escapeHtml(i)}</li>`).join('')
      : '<li style="font-style:italic;color:var(--text-tertiary)">No architectural deductions generated.</li>';
  }

  const missingList = document.getElementById('list-missing');
  if (missingList) {
    missingList.innerHTML = missing.length
      ? missing.map(cleanFactTag).map(m => `<li>${escapeHtml(m)}</li>`).join('')
      : '<li style="font-style:italic;color:var(--text-tertiary)">No unanswered questions flagged.</li>';
  }
}

function cleanFactTag(str) {
  if (!str) return '';
  return str.replace(/^\[(KNOWN|INFERRED|MISSING)\]\s*/i, '').trim();
}

// --------------------------------------------------------------------------
// Next-Best Question Callout
// --------------------------------------------------------------------------
function renderNextBestQuestion(data) {
  const nbq = data.next_best_question || {};
  const qText = document.getElementById('next-q-text');
  const qImpact = document.getElementById('next-q-impact');
  const qRationale = document.getElementById('next-q-rationale');
  const optionsBox = document.getElementById('next-q-options');
  const applyBtn = document.getElementById('btn-apply-answer');

  if (qText) {
    qText.textContent = nbq.question || 'What is the expected daily volume of inbound lead inquiries?';
  }
  if (qImpact) {
    qImpact.textContent = nbq.impact ? `Impact: ${nbq.impact}` : 'Impact: Architecture & SLA';
  }
  if (qRationale) {
    qRationale.textContent = nbq.impact 
      ? `Resolving this locks down: ${nbq.impact}`
      : 'Resolving this locks down whether standard schema parsers or dedicated queue workers are required.';
  }

  selectedOptionText = null;
  if (applyBtn) applyBtn.disabled = true;

  const options = nbq.options || [
    'Sub-2s response SLA (< 2s execution)',
    'Strict human review queue before CRM insertion',
    'Batch nightly execution with summary report'
  ];

  if (optionsBox) {
    optionsBox.innerHTML = options.map((opt) => `
      <button class="decision-opt-btn" data-val="${escapeHtml(opt)}">
        <span class="decision-radio"></span>
        <span>${escapeHtml(opt)}</span>
      </button>
    `).join('');

    optionsBox.querySelectorAll('.decision-opt-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        optionsBox.querySelectorAll('.decision-opt-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedOptionText = btn.dataset.val;
        if (applyBtn) applyBtn.disabled = false;
      });
    });
  }
}

function applyClarifyingAnswer() {
  if (!selectedOptionText) return;

  const briefEl = document.getElementById('input-brief');
  briefEl.value += `\n\n[Clarification]: Client confirmed: "${selectedOptionText}".`;
  document.getElementById('brief-char-count').textContent = `${briefEl.value.length} characters`;

  showToast(`Applied: "${selectedOptionText.slice(0, 30)}..."`);
  analyzeOpportunity();
}

// --------------------------------------------------------------------------
// Review Council & Evidence-Based Readiness
// --------------------------------------------------------------------------
function renderReviewAndReadiness(data) {
  const readiness = data.readiness_assessment || { score: 85, status: "Ready for Review", checks: [] };

  const scoreEl = document.getElementById('readiness-score');
  if (scoreEl) scoreEl.textContent = readiness.score;

  const statusEl = document.getElementById('readiness-status');
  if (statusEl) statusEl.textContent = readiness.status;

  // Breakdown grid
  const breakdownBox = document.getElementById('readiness-breakdown');
  if (breakdownBox) {
    const checks = readiness.checks || [];
    breakdownBox.innerHTML = checks.map(c => `
      <div class="check-item">
        <div class="check-top">
          <span class="check-name">${c.passed ? '✓' : '✗'} ${escapeHtml(c.name)}</span>
          <span class="check-pts">${c.score}/${c.max}</span>
        </div>
        <span class="check-detail">${escapeHtml(c.detail)}</span>
      </div>
    `).join('');
  }

  // 3 Structured Review Passes
  const reviewChecks = data.review_checks || [];
  reviewChecks.forEach(rc => {
    let targetV = null;
    let targetN = null;
    if (rc.id === 'technical_feasibility') {
      targetV = document.getElementById('verdict-tech');
      targetN = document.getElementById('notes-tech');
    } else if (rc.id === 'security_data_risks') {
      targetV = document.getElementById('verdict-sec');
      targetN = document.getElementById('notes-sec');
    } else if (rc.id === 'business_value') {
      targetV = document.getElementById('verdict-val');
      targetN = document.getElementById('notes-val');
    }

    if (targetV) {
      targetV.textContent = rc.verdict;
      const vUpper = (rc.verdict || '').toUpperCase();
      if (vUpper.includes('PASS')) {
        targetV.className = 'pass-verdict verdict-pass';
      } else if (vUpper.includes('NOT') || vUpper.includes('N/A')) {
        targetV.className = 'pass-verdict verdict-na';
      } else {
        targetV.className = 'pass-verdict verdict-review';
      }
    }
    if (targetN) targetN.textContent = rc.notes;
  });

  // Operational Risks
  const risksList = document.getElementById('disp-risks');
  if (risksList) {
    const risks = data.risks || [];
    risksList.innerHTML = risks.length
      ? risks.map(r => `<li>${escapeHtml(r)}</li>`).join('')
      : '<li>No severe operational risks identified.</li>';
  }
}

// --------------------------------------------------------------------------
// Export & Share
// --------------------------------------------------------------------------
function copyProposal() {
  if (!latestProposal) {
    showToast('Generate a proposal first.');
    return;
  }
  const md = buildMarkdown(latestProposal);
  navigator.clipboard.writeText(md).then(() => {
    showToast('Copied proposal to clipboard.');
  }).catch(() => {
    showToast('Clipboard access denied.');
  });
}

function exportMarkdown() {
  if (!latestProposal) {
    showToast('Generate a proposal first.');
    return;
  }
  const md = buildMarkdown(latestProposal);
  const blob = new Blob([md], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `cynbit-opportunity-proposal-${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Downloaded proposal (.md).');
}

function exportJson() {
  if (!latestProposal) {
    showToast('Generate a proposal first.');
    return;
  }
  const blob = new Blob([JSON.stringify(latestProposal, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `cynbit-blueprint-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Downloaded blueprint JSON.');
}

function buildMarkdown(d) {
  return `# Cynbit AI Opportunity Proposal
**Category:** ${d.opportunity_type || 'AI Solution Architecture'}  
**Execution Mode:** ${d.mode || 'LangGraph Orchestrated'}  

---

## 01 — Current Situation & Problem
${d.problem_statement || 'N/A'}

## 02 — Fact & Gap Analysis
### [KNOWN] Stated in Brief
${(d.known_facts || []).map(f => `- ${f}`).join('\n')}

### [INFERRED] Architectural Deductions
${(d.inferred_implications || d.understood_implications || []).map(i => `- ${i}`).join('\n')}

### [MISSING] Unanswered Questions & Blind Spots
${(d.missing_information || []).map(m => `- ${m}`).join('\n')}

## 03 — Recommended Approach & Target Architecture
**Summary:** ${d.executive_summary || 'N/A'}

**Recommended Strategy:** ${d.recommended_solution || 'N/A'}

**Target Architecture:**
\`\`\`
${d.architecture || 'Inbound Ingestion -> Schema Validation -> Deterministic Gate -> Grounded LLM -> Human Review Queue -> Destination'}
\`\`\`

### Step-by-Step Technical Execution
${(d.workflow || []).map((w, idx) => `${idx + 1}. ${w}`).join('\n')}

## 04 — Phased Implementation & Success Criteria
${(d.implementation_plan || []).map(p => `- **${p.phase}:** ${p.deliverable}`).join('\n')}

### Measurable Acceptance Metrics
${(d.evaluation_metrics || []).map(m => `- ${m}`).join('\n')}

### Data Requirements
${(d.data_requirements || []).map(d => `- ${d}`).join('\n')}

## 05 — Governance, Risks & Review Council
**Proposal Completeness:** ${d.completeness_assessment ? d.completeness_assessment.score : (d.readiness_assessment ? d.readiness_assessment.score : 'N/A')}/100 (${d.completeness_assessment ? d.completeness_assessment.status : (d.readiness_assessment ? d.readiness_assessment.status : 'N/A')})
*(Based on requirements coverage, architecture completeness, unresolved critical questions, and governance checks.)*

### Structured Review Passes
${(d.review_checks || []).map(r => `- **${r.name} [${r.verdict}]:** ${r.notes}`).join('\n')}

### Identified Operational Risks
${(d.risks || []).map(r => `- [Risk] ${r}`).join('\n')}
`;
}

// --------------------------------------------------------------------------
// Toast & Utilities
// --------------------------------------------------------------------------
function showToast(msg) {
  const box = document.getElementById('toast-box');
  if (!box) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  box.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
