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

const threatInput   = $("threatInput");
const analyzeBtn    = $("analyzeBtn");
const charCount     = $("charCount");
const resultsSection = $("resultsSection");
const loadingOverlay = $("loadingOverlay");
const errorBanner   = $("errorBanner");
const errorText     = $("errorText");
const errorDismiss  = $("errorDismiss");
const elapsedBadge  = $("elapsedBadge");
const statusDot     = $("statusDot");
const statusLabel   = $("statusLabel");
const headerConfig  = $("headerConfig");
const judgeCardCopy = $("judgeCardCopy");

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
      statusLabel.textContent = "API connected";
    } else {
      statusDot.classList.add("error");
      statusLabel.textContent = "API key missing";
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
    headerConfig.innerHTML = Object.entries({
      "A": data.agents.classifier,
      "B": data.agents.vuln_analyst,
      "C": data.agents.impact,
      "J": data.agents.judge,
    }).map(([k, v]) => `<div class="config-chip"><span>[${k}]</span> ${v}</div>`).join("");

    // update agent provider labels in cards
    $("providerA").textContent     = data.agents.classifier  || "";
    $("providerB").textContent     = data.agents.vuln_analyst || "";
    $("providerC").textContent     = data.agents.impact       || "";
    $("providerJudge").textContent = data.agents.judge        || "";
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
      const text = EXAMPLES[btn.dataset.example] || "";
      threatInput.value = text;
      threatInput.dispatchEvent(new Event("input"));
      threatInput.focus();
    });
  });

  // Analyse button
  analyzeBtn.addEventListener("click", runAnalysis);

  // Ctrl+Enter in textarea
  threatInput.addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!analyzeBtn.disabled) runAnalysis();
    }
  });

  // Error dismiss
  errorDismiss.addEventListener("click", () => {
    errorBanner.hidden = true;
  });

  // Copy judge report
  judgeCardCopy.addEventListener("click", copyJudgeReport);
}

// ── Loading step animation ────────────────────────────────────

const STEP_IDS    = ["step1", "step2", "step3", "step4"];
const STEP_LABELS = [
  "Agent A — Classifying threat…",
  "Agent B — Mapping CVE & MITRE…",
  "Agent C — Assessing impact…",
  "Judge — Synthesising report…",
];

let stepTimer = null;

function startLoadingSteps() {
  let i = 0;
  STEP_IDS.forEach(id => {
    $(id).className = "loading-step";
  });
  $("loadingLabel").textContent = STEP_LABELS[0];

  function advance() {
    if (i > 0) $(STEP_IDS[i - 1]).classList.add("done");
    if (i < STEP_IDS.length) {
      $(STEP_IDS[i]).classList.add("active");
      $("loadingLabel").textContent = STEP_LABELS[i] || "Finalising…";
      i++;
      stepTimer = setTimeout(advance, 4500 + Math.random() * 2000);
    }
  }
  advance();
}

function stopLoadingSteps() {
  clearTimeout(stepTimer);
  STEP_IDS.forEach(id => {
    const el = $(id);
    el.classList.remove("active");
    el.classList.add("done");
  });
}

// ── Main analysis call ────────────────────────────────────────

async function runAnalysis() {
  const threat = threatInput.value.trim();
  if (threat.length < 10) return;

  // Reset state
  errorBanner.hidden = true;
  setAgentState("waiting");
  elapsedBadge.hidden = true;

  // Show results area with loading overlay
  resultsSection.hidden  = false;
  loadingOverlay.hidden  = false;
  analyzeBtn.disabled    = true;
  analyzeBtn.querySelector(".btn-text").textContent = "Analysing…";
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  startLoadingSteps();

  try {
    const res  = await fetch(`${API_BASE}/api/analyze`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ threat }),
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || `Server error ${res.status}`);
    }

    stopLoadingSteps();
    renderResults(data);
  } catch (err) {
    stopLoadingSteps();
    showError(err.message || "Failed to connect to the analysis server.");
    loadingOverlay.hidden = true;
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.querySelector(".btn-text").textContent = "Analyze Threat";
  }
}

// ── Render results ────────────────────────────────────────────

function renderResults(data) {
  loadingOverlay.hidden = true;

  // Agent outputs
  const agents = data.agent_outputs || [];
  const map = { "Threat Classifier": "A", "Vulnerability Analyst": "B", "Impact Assessor": "C" };

  agents.forEach(agent => {
    const key = map[agent.agent];
    if (!key) return;
    $(`output${key}`).textContent = agent.output || "(no output)";
    $(`provider${key}`).textContent = agent.provider || "";
    $(`status${key}`).textContent = "✓";
    $(`card${key}`).classList.add("ready");
  });

  // Judge output
  $("judgeOutput").textContent = data.final_report || "(no report)";
  $("providerJudge").textContent = agents[0] ? "" : "";

  // Elapsed badge
  if (data.elapsed_sec) {
    elapsedBadge.hidden = false;
    elapsedBadge.textContent = `⏱ ${data.elapsed_sec}s`;
  }
}

// ── Reset agent card states ────────────────────────────────────

function setAgentState(state) {
  ["A", "B", "C"].forEach(k => {
    $(`card${k}`).classList.remove("ready");
    $(`status${k}`).textContent = "";
    $(`output${k}`).textContent = state === "waiting" ? "Waiting for analysis…" : "";
  });
  $("judgeOutput").textContent = "Judge synthesis will appear here after all agents complete.";
}

// ── Error display ─────────────────────────────────────────────

function showError(msg) {
  errorText.textContent = msg;
  errorBanner.hidden    = false;
  resultsSection.hidden = true;
}

// ── Copy judge report to clipboard ────────────────────────────

async function copyJudgeReport() {
  const text = $("judgeOutput").textContent;
  if (!text || text.includes("synthesis will appear")) return;
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
