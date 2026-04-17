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

const threatInput          = $("threatInput");
const analyzeBtn           = $("analyzeBtn");
const charCount            = $("charCount");
const resultsSection       = $("resultsSection");
const loadingOverlay       = $("loadingOverlay");
const errorBanner          = $("errorBanner");
const errorText            = $("errorText");
const errorDismiss         = $("errorDismiss");
const elapsedBadge         = $("elapsedBadge");
const statusDot            = $("statusDot");
const statusLabel          = $("statusLabel");
const headerConfig         = $("headerConfig");
const judgeCardCopy        = $("judgeCardCopy");
const clarificationSection = $("clarificationSection");
const clarificationQuestions = $("clarificationQuestions");
const answersInput         = $("answersInput");
const submitAnswersBtn     = $("submitAnswersBtn");
const rejectionBanner      = $("rejectionBanner");
const rejectionReason      = $("rejectionReason");
const rejectionDismiss     = $("rejectionDismiss");
const draftToggle          = $("draftToggle");
const draftCard            = $("draftCard");

// Mapping: agent name → card suffix
const AGENT_MAP = {
  "Threat Classifier":    "A",
  "Vulnerability Analyst": "B",
  "Impact Assessor":      "C",
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

// ── Config chips ───────────────────────────────────────────────

async function loadConfig() {
  try {
    const res  = await fetch(`${API_BASE}/api/config`);
    const data = await res.json();
    if (!data.agents) return;

    const chips = {
      "0": data.agents.validator,
      "A": data.agents.classifier,
      "B": data.agents.vuln_analyst,
      "C": data.agents.impact,
      "D": data.agents.remediation,
      "J": data.agents.judge,
    };
    headerConfig.innerHTML = Object.entries(chips)
      .map(([k, v]) => `<div class="config-chip"><span>[${k}]</span> ${v}</div>`)
      .join("");

    // Update agent provider labels in cards (both rounds)
    $("providerA").textContent  = $("providerA2").textContent  = data.agents.classifier   || "";
    $("providerB").textContent  = $("providerB2").textContent  = data.agents.vuln_analyst  || "";
    $("providerC").textContent  = $("providerC2").textContent  = data.agents.impact        || "";
    $("providerD").textContent  = $("providerD2").textContent  = data.agents.remediation   || "";
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

  // Draft report collapse toggle
  draftToggle.addEventListener("click", () => {
    const collapsed = draftCard.hidden;
    draftCard.hidden = !collapsed;
    draftToggle.textContent = collapsed ? "▼ Collapse" : "▶ Expand";
  });
}

// ── Loading step animation ────────────────────────────────────

const STEP_IDS = ["lstep0", "lstep1", "lstep2", "lstep3", "lstep4"];
const STEP_LABELS = [
  "Validator — checking & enriching input…",
  "Round 1 — 4 agents analysing in parallel…",
  "Judge — drafting Round 1 report…",
  "Round 2 — agents refining with draft context…",
  "Judge — synthesising final report…",
];
// Rough timing per step (ms) — for visual progression
const STEP_DURATIONS = [8000, 60000, 40000, 60000, 40000];

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
  errorBanner.hidden       = true;
  rejectionBanner.hidden   = true;
  clarificationSection.hidden = true;
  elapsedBadge.hidden      = true;
  resetCards();

  // Show loading
  resultsSection.hidden  = false;
  loadingOverlay.hidden  = false;
  analyzeBtn.disabled    = true;
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
      loadingOverlay.hidden   = true;
      resultsSection.hidden   = true;
      showClarification(data.questions);
      return;
    }

    if (data.status === "rejected") {
      loadingOverlay.hidden   = true;
      resultsSection.hidden   = true;
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
  loadingOverlay.hidden = true;
  clarificationSection.hidden = true;

  // Round 1 outputs
  (data.round1_outputs || []).forEach(agent => {
    const key = AGENT_MAP[agent.agent];
    if (!key) return;
    $(`output${key}`).textContent   = agent.output   || "(no output)";
    $(`provider${key}`).textContent = agent.provider || "";
    $(`status${key}`).textContent   = "✓";
    $(`card${key}`).classList.add("ready");
  });

  // Draft report
  $("draftOutput").textContent = data.draft_report || "(no draft report)";

  // Round 2 outputs
  (data.round2_outputs || []).forEach(agent => {
    const key = AGENT_MAP[agent.agent];
    if (!key) return;
    $(`output${key}2`).textContent   = agent.output   || "(no output)";
    $(`provider${key}2`).textContent = agent.provider || "";
    $(`status${key}2`).textContent   = "✓";
    $(`card${key}2`).classList.add("ready");
  });

  // Final report
  $("judgeOutput").textContent = data.final_report || "(no final report)";

  // Elapsed badge
  if (data.elapsed_sec) {
    elapsedBadge.hidden = false;
    elapsedBadge.textContent = `⏱ ${data.elapsed_sec}s`;
  }

  // Scroll to final report
  $("judgeCard").scrollIntoView({ behavior: "smooth", block: "start" });
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

// ── Rejection ────────────────────────────────────────────────

function showRejection(reason) {
  rejectionReason.textContent = reason || "The input does not describe a cybersecurity threat.";
  rejectionBanner.hidden = false;
  rejectionBanner.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Reset card states ─────────────────────────────────────────

function resetCards() {
  ["A", "B", "C", "D"].forEach(k => {
    [$(`card${k}`), $(`card${k}2`)].forEach(card => {
      if (card) card.classList.remove("ready");
    });
    [$(`status${k}`), $(`status${k}2`)].forEach(el => {
      if (el) el.textContent = "";
    });
    [$(`output${k}`), $(`output${k}2`)].forEach(el => {
      if (el) el.textContent = "Waiting…";
    });
  });
  $("draftOutput").textContent  = "Draft report will appear here after Round 1 completes.";
  $("judgeOutput").textContent  = "Final report will appear here after Round 2 completes.";
  draftCard.hidden = false;
  draftToggle.textContent = "▼ Collapse";
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
