/* ─────────────────────────────────────────────────────────────
   CyberCouncil — Frontend Application Logic
   Communicates with the Flask server at /api/*
───────────────────────────────────────────────────────────── */

const API_BASE = "";   // same origin

// ── Example threat presets ────────────────────────────────────

const EXAMPLES = {
  phishing: `An employee received an email from ceo-financials.com claiming to be the CEO, requesting an urgent wire transfer of $150,000 to an external account. The link in the email points to http://docusign-secure.ceo-financials.com/sign. Email was sent at 2:47 AM. The real company domain is company.com.`,

  ransomware: `All files on the company network share are encrypted and renamed with a .locked extension. A ransom note named README_DECRYPT.txt demands $500,000 in Bitcoin within 72 hours or decryption keys will be permanently destroyed. Backup servers also appear to be encrypted.`,

  sqli: `The web application's login form is receiving the payload: admin' OR '1'='1'; DROP TABLE users; -- . WAF logs also show attempts like: UNION SELECT username, password FROM admin_users-- targeting the MySQL backend. Database error messages are being returned in HTTP responses.`,

  ddos: `The public API gateway is receiving 847 requests per second from approximately 1,200 different IP addresses across 40 countries. All legitimate user traffic is being blocked. Load balancer CPU is at 100% and upstream ISP confirms volumetric traffic anomaly reaching 150 Gbps.`,

  malware: `Antivirus detects outbound traffic to 185.220.101.x at irregular intervals. System processes are silently spawning cmd.exe and powershell.exe with base64-encoded payloads. Mimikatz artifacts found on three workstations. DNS queries to algorithmically generated subdomains detected — consistent with a DGA C2 beacon.`,
};

// ── DOM refs ──────────────────────────────────────────────────

const $ = id => document.getElementById(id);

const threatInput            = $("threatInput");
const analyzeBtn             = $("analyzeBtn");
const charCount              = $("charCount");
const resultsSection         = $("resultsSection");
const loadingOverlay         = $("loadingOverlay");
const errorBanner            = $("errorBanner");
const errorText              = $("errorText");
const errorDismiss           = $("errorDismiss");
const elapsedBadge           = $("elapsedBadge");
const statusDot              = $("statusDot");
const statusLabel            = $("statusLabel");
const headerConfig           = $("headerConfig");
const judgeCardCopy          = $("judgeCardCopy");
const clarificationSection   = $("clarificationSection");
const clarificationQuestions = $("clarificationQuestions");
const answersInput           = $("answersInput");
const submitAnswersBtn       = $("submitAnswersBtn");
const rejectionBanner        = $("rejectionBanner");
const rejectionReason        = $("rejectionReason");
const rejectionDismiss       = $("rejectionDismiss");
const consensusToggle        = $("consensusToggle");
const consensusPanel         = $("consensusPanel");
const disagreementLabel      = $("disagreementLabel");

// ── Agent name → card key mapping ────────────────────────────
// Card IDs: card{KEY}

const AGENT_MAP = {
  "Threat Classifier":    "A",
  "Threat Classifier-2":  "As",   // consensus secondary
  "Vulnerability Analyst":"B",
  "Impact Assessor":      "C",
  "Impact Assessor-2":    "Cs",   // consensus secondary
  "Remediation Engineer": "D",
};

// ── Initialise ────────────────────────────────────────────────

(async function init() {
  await checkHealth();
  loadConfig();
  bindEvents();
})();

// ── Health check ──────────────────────────────────────────────

async function checkHealth() {
  try {
    const res  = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    if (data.status === "ok") {
      statusDot.classList.add("ok");
      const count = data.models ? data.models.length : 0;
      statusLabel.textContent = `Ollama connected · ${count} model${count !== 1 ? "s" : ""} loaded`;
    } else {
      statusDot.classList.add("error");
      statusLabel.textContent = "Ollama offline";
    }
  } catch {
    statusDot.classList.add("error");
    statusLabel.textContent = "Server offline";
  }
}

// ── Config chips ──────────────────────────────────────────────

async function loadConfig() {
  try {
    const res  = await fetch(`${API_BASE}/api/config`);
    const data = await res.json();
    if (!data.agents) return;

    const chips = {
      "0":  data.agents.validator,
      "A":  data.agents.classifier,
      "A₂": data.agents.classifier_2,
      "B":  data.agents.vuln_analyst,
      "C":  data.agents.impact,
      "C₂": data.agents.impact_2,
      "D":  data.agents.remediation,
      "J":  data.agents.judge,
    };
    headerConfig.innerHTML = Object.entries(chips)
      .map(([k, v]) => `<div class="config-chip"><span>[${k}]</span> ${v || "—"}</div>`)
      .join("");

    // Pre-fill provider labels on all agent cards (both rounds)
    const fill = (ids, val) => ids.forEach(id => { const el = $(id); if (el) el.textContent = val || ""; });
    fill(["providerA",  "providerA2"],  data.agents.classifier);
    fill(["providerAs", "providerAs2"], data.agents.classifier_2);
    fill(["providerB",  "providerB2"],  data.agents.vuln_analyst);
    fill(["providerC",  "providerC2"],  data.agents.impact);
    fill(["providerCs", "providerCs2"], data.agents.impact_2);
    fill(["providerD",  "providerD2"],  data.agents.remediation);
  } catch { /* non-critical */ }
}

// ── Event bindings ────────────────────────────────────────────

function bindEvents() {
  // Character counter + button enable
  threatInput.addEventListener("input", () => {
    const len = threatInput.value.length;
    charCount.textContent = len;
    charCount.parentElement.className
      = len > 3800 ? "char-count limit"
      : len > 3200 ? "char-count warn"
      : "char-count";
    analyzeBtn.disabled = len < 10;
  });

  // Example chips
  document.querySelectorAll(".example-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      threatInput.value = EXAMPLES[btn.dataset.example] || "";
      threatInput.dispatchEvent(new Event("input"));
      threatInput.focus();
    });
  });

  // Analyse button
  analyzeBtn.addEventListener("click", () => runAnalysis());

  // Ctrl+Enter in textarea
  threatInput.addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!analyzeBtn.disabled) runAnalysis();
    }
  });

  // Submit clarification answers
  submitAnswersBtn.addEventListener("click", () => {
    const answers = answersInput.value.trim();
    if (!answers) return;
    runAnalysis(answers);
  });

  // Error dismiss
  errorDismiss.addEventListener("click", () => { errorBanner.hidden = true; });

  // Rejection dismiss
  rejectionDismiss.addEventListener("click", () => { rejectionBanner.hidden = true; });

  // Copy judge report
  judgeCardCopy.addEventListener("click", copyFinalReport);

  // Consensus panel collapse toggle
  consensusToggle.addEventListener("click", () => {
    const collapsed = consensusPanel.hidden;
    consensusPanel.hidden = !collapsed;
    consensusToggle.textContent = collapsed ? "▼ Collapse" : "▶ Expand";
  });
}

// ── Loading step animation ────────────────────────────────────

const STEP_IDS = ["lstep0", "lstep1", "lstep2"];
const STEP_LABELS = [
  "Validator — checking & enriching input…",
  "6 agents analysing in parallel…",
  "Judge — synthesising final report…",
];
const STEP_DURATIONS = [8000, 60000, 40000];

let stepTimer = null;

function startLoadingSteps() {
  STEP_IDS.forEach(id => { $(id).className = "loading-step"; });
  $("loadingLabel").textContent = STEP_LABELS[0];
  let i = 0;

  function advance() {
    if (i > 0) $(STEP_IDS[i - 1]).classList.add("done");
    if (i < STEP_IDS.length) {
      $(STEP_IDS[i]).classList.add("active");
      $("loadingLabel").textContent = STEP_LABELS[i];
      i++;
      stepTimer = setTimeout(advance, STEP_DURATIONS[i - 1]);
    }
  }
  advance();
}

function stopLoadingSteps() {
  clearTimeout(stepTimer);
  STEP_IDS.forEach(id => {
    $(id).classList.remove("active");
    $(id).classList.add("done");
  });
  $("loadingLabel").textContent = "Analysis complete.";
}

// ── Main analysis call ────────────────────────────────────────

async function runAnalysis(userAnswers = "") {
  const threat = threatInput.value.trim();
  if (threat.length < 10) return;

  // Reset all state
  errorBanner.hidden          = true;
  rejectionBanner.hidden      = true;
  clarificationSection.hidden = true;
  elapsedBadge.hidden         = true;
  disagreementLabel.hidden    = true;
  consensusPanel.hidden       = true;
  resetCards();

  // Show loading
  resultsSection.hidden = false;
  loadingOverlay.hidden = false;
  analyzeBtn.disabled   = true;
  analyzeBtn.querySelector(".btn-text").textContent = "Analysing…";
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  startLoadingSteps();

  try {
    const body = { threat };
    if (userAnswers) body.user_answers = userAnswers;

    const res  = await fetch(`${API_BASE}/api/analyze`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
    });

    const data = await res.json();
    stopLoadingSteps();

    if (!res.ok || data.error) {
      throw new Error(data.error || `Server error ${res.status}`);
    }

    if (data.status === "needs_clarification") {
      loadingOverlay.hidden = true;
      resultsSection.hidden = true;
      showClarification(data.questions);
      return;
    }

    if (data.status === "rejected") {
      loadingOverlay.hidden = true;
      resultsSection.hidden = true;
      showRejection(data.reason);
      return;
    }

    renderResults(data);

  } catch (err) {
    stopLoadingSteps();
    loadingOverlay.hidden = true;
    resultsSection.hidden = true;
    showError(err.message || "Failed to connect to the analysis server.");
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.querySelector(".btn-text").textContent = "Analyze Threat";
  }
}

// ── Render results ────────────────────────────────────────────

function renderResults(data) {
  loadingOverlay.hidden       = true;
  clarificationSection.hidden = true;

  // Agent outputs — fill all 6 agent cards
  (data.agent_outputs || []).forEach(agent => {
    const key = AGENT_MAP[agent.agent];
    if (!key) return;
    $(`output${key}`).textContent   = agent.output   || "(no output)";
    $(`provider${key}`).textContent = agent.provider || "";
    $(`status${key}`).textContent   = "✓";
    $(`card${key}`).classList.add("ready");
  });

  // Final report
  $("judgeOutput").textContent = data.final_report || "(no final report)";

  // Elapsed badge
  if (data.elapsed_sec) {
    elapsedBadge.hidden      = false;
    elapsedBadge.textContent = `⏱ ${data.elapsed_sec}s`;
  }

  // Disagreement log panel
  renderDisagreementLog(data.disagreement_log || {});

  // Scroll to final report
  $("judgeCard").scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Disagreement log panel ────────────────────────────────────

function renderDisagreementLog(log) {
  if (!log || (!log.classification && !log.severity)) return;

  const cl = log.classification || {};
  const sv = log.severity       || {};
  // Classification row
  $("clA1").textContent = cl.agent_a_primary   || "—";
  $("clA2").textContent = cl.agent_a_secondary || "—";
  const clVerdict = $("clVerdict");
  if (cl.disagree) {
    clVerdict.innerHTML = `<span class="verdict conflict">⚡ CONFLICT — judge resolved</span>`;
  } else {
    clVerdict.innerHTML = `<span class="verdict agree">✓ AGREEMENT — high confidence</span>`;
  }

  // Severity row
  $("svC1").textContent = sv.agent_c_primary   != null ? sv.agent_c_primary   : "—";
  $("svC2").textContent = sv.agent_c_secondary != null ? sv.agent_c_secondary : "—";
  const svVerdict = $("svVerdict");
  if (sv.disagree) {
    svVerdict.innerHTML = `<span class="verdict conflict">⚡ CONFLICT — judge resolved</span>`;
  } else {
    svVerdict.innerHTML = `<span class="verdict agree">✓ AGREEMENT — high confidence</span>`;
  }

  // Show panel
  disagreementLabel.hidden = false;
  consensusPanel.hidden    = false;
  consensusToggle.textContent = "▼ Collapse";
}

// ── Clarification flow ────────────────────────────────────────

function showClarification(questions) {
  clarificationQuestions.innerHTML = (questions || [])
    .map((q, i) => `<div class="question-item"><span class="question-num">${i + 1}.</span><span>${q}</span></div>`)
    .join("");
  answersInput.value = "";
  clarificationSection.hidden = false;
  clarificationSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Rejection ─────────────────────────────────────────────────

function showRejection(reason) {
  rejectionReason.textContent = reason || "The input does not describe a cybersecurity threat.";
  rejectionBanner.hidden = false;
  rejectionBanner.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Reset card states ─────────────────────────────────────────

function resetCards() {
  ["A", "As", "B", "C", "Cs", "D"].forEach(k => {
    const card = $(`card${k}`);
    if (card) card.classList.remove("ready", "revised");
    const status = $(`status${k}`);
    if (status) status.textContent = "";
    const output = $(`output${k}`);
    if (output) output.textContent = "Waiting…";
  });
  $("judgeOutput").textContent = "Final report will appear here after analysis completes.";
}

// ── Error display ─────────────────────────────────────────────

function showError(msg) {
  errorText.textContent = msg;
  errorBanner.hidden    = false;
}

// ── Copy final report to clipboard ───────────────────────────

async function copyFinalReport() {
  const text = $("judgeOutput").textContent;
  if (!text || text.includes("will appear here")) return;
  try {
    await navigator.clipboard.writeText(text);
    judgeCardCopy.textContent = "✓ Copied";
    judgeCardCopy.classList.add("copied");
    setTimeout(() => {
      judgeCardCopy.textContent = "⧉ Copy";
      judgeCardCopy.classList.remove("copied");
    }, 2000);
  } catch {
    judgeCardCopy.textContent = "Failed";
    setTimeout(() => { judgeCardCopy.textContent = "⧉ Copy"; }, 2000);
  }
}
