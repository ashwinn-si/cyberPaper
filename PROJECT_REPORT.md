# CyberCouncil — Complete Project Report

**System:** Multi-Agent LLM Framework for Cybersecurity Threat Detection and Analysis  
**Target Venue:** IEEE Conference on Cybersecurity  
**Hardware:** RTX 5060 Ti (16GB VRAM + 18GB shared = 34GB GPU-accessible), 32GB RAM, Intel Core Ultra 9

---

## 1. Project Overview

CyberCouncil is a multi-agent LLM system that routes cybersecurity threat descriptions through a pipeline of specialized agents, then arbitrates their outputs through a CISO-role judge agent to produce a final actionable threat assessment.

**Core research claims:**
1. Multi-agent consensus with cross-model pairs improves threat classification reliability
2. Judge arbitration with explicit disagreement resolution outperforms majority voting
3. Agents that revise their position after seeing a draft report (Round 2) carry stronger signal — weighted accordingly
4. The provider pattern allows full LLM ablation studies with zero code changes

---

## 2. System Architecture

### 2.1 Pipeline Flow

```
Raw Threat Input (user-submitted)
        ↓
┌──────────────────────────────────────┐
│  Agent 0: Validator                  │
│  Pass 1: relevance + specificity     │
│  Pass 2: enrich (if clarification    │
│          questions were answered)    │
└──────────────┬───────────────────────┘
               ↓ Enriched threat
┌──────────────────────────────────────────────────────────┐
│                   ROUND 1 — Parallel                     │
│                                                          │
│  Agent A   (DeepSeek-R1)  Threat Classifier ─────┐      │
│  Agent A₂  (Qwen2.5-7B)   Classifier (consensus) ┤      │
│  Agent B   (Mistral-Nemo) Vuln Analyst ───────────┼──→  │
│  Agent C   (DeepSeek-R1)  Impact Assessor ────────┤      │
│  Agent C₂  (Qwen2.5-7B)   Impact (consensus) ─────┤      │
│  Agent D   (Mistral-Nemo) Remediation Engineer ───┘      │
│                                                          │
│  All 6 run via asyncio.gather() — ~3–5 sec wall-clock    │
└──────────────────────┬───────────────────────────────────┘
                       ↓
     Disagreement detection (in-process, <0.1 sec)
       • A vs A₂ → classification_conflict flag
       • C vs C₂ → severity_conflict flag (if gap > 2 points)
       → disagreement_log built
                       ↓
     Judge (Qwen2.5-72B) — Round 1
       receives: 6 agent outputs + disagreement_log
       produces: draft report
                       ↓
┌──────────────────────────────────────────────────────────┐
│              ROUND 2 — Parallel (sees draft)             │
│  All 6 agents re-analyze with judge's draft as context   │
└──────────────────────┬───────────────────────────────────┘
                       ↓
     Round-change detection (in-process)
       • agents that revised their core position → weight 1.5
       • stable agents → weight 1.0
       → round_weights built
                       ↓
     Judge (Qwen2.5-72B) — Round 2
       receives: 6 Round 2 outputs + disagreement_log + round_weights
       produces: final SOC-ready report
```

### 2.2 Why Two Rounds

Round 1 gives the judge a diverse first-pass. The judge's draft report becomes context for Round 2 — agents that genuinely update their analysis (not just echo the draft) are flagged as "revised" and weighted 1.5×. This distinguishes active reasoning from anchoring bias and gives the judge a signal about which outputs are deliberate revisions vs. stable conclusions.

### 2.3 Disagreement Log (Novel Contribution)

After Round 1, the orchestrator computes:

```json
{
  "classification": {
    "agent_a_primary":   "phishing",
    "agent_a_secondary": "malware",
    "disagree":          true
  },
  "severity": {
    "agent_c_primary":   7,
    "agent_c_secondary": 4,
    "disagree":          true
  },
  "round_changes": {
    "Threat Classifier":   {"changed": false, "weight": 1.0},
    "Threat Classifier-2": {"changed": true,  "weight": 1.5},
    "Impact Assessor":     {"changed": true,  "weight": 1.5},
    ...
  }
}
```

The judge receives explicit conflict directives:
- `"CLASSIFICATION CONFLICT: Classifier-1=phishing vs Classifier-2=malware — you MUST resolve this."`
- `"SEVERITY AGREEMENT: both impact agents agree on score 7 — high confidence."`

This makes contradiction resolution **auditable** — each conflict in the judge's output maps to a logged disagreement.

---

## 3. Agent Specifications

### Agent 0 — Validator
**File:** `agents/validator_agent.py`  
**Provider:** Llama-3 (8B, `max_tokens=800`)  
**Role:** Gatekeeps the pipeline. Runs before any analysis agent.

**Two-pass system:**
- **Pass 1 (raw input):** Evaluates relevance, specificity, clarity. Returns one of:
  - `STATUS: Invalid` — not a security threat
  - `STATUS: Needs Clarification` — up to 3 targeted questions
  - `STATUS: Pass` — enriched threat description (2–4 sentences, professional terminology)
- **Pass 2 (original + user answers):** Always produces `STATUS: Pass`. Merges all context.

**Question priority order (prompt-enforced):**
1. Attack vector (how did the attacker gain access?)
2. Observable symptoms (what errors/alerts were seen?)
3. Affected systems/scope (what is impacted?)

---

### Agent A — Threat Classifier (Primary)
**File:** `agents/classifier_agent.py`  
**Provider:** DeepSeek-R1  
**Prompt:** `prompts/prompt_a.txt`

**Output format:**
```
THREAT CATEGORY: <one of 9 canonical labels>
CONFIDENCE SCORE: <0–100%>
JUSTIFICATION: <one sentence referencing specific indicators>
```

**Canonical labels:** Phishing | Malware | SQL Injection | DDoS | Ransomware | Zero-Day Exploit | Insider Threat | Man-in-the-Middle | Other

**Constraints:** Cannot discuss CVEs, impacts, severity, or remediation.

---

### Agent A₂ — Threat Classifier (Consensus Secondary)
**File:** `agents/classifier_agent_2.py`  
**Provider:** Qwen2.5 (7B)  
**Prompt:** Same as Agent A (`prompts/prompt_a.txt`)  
**Purpose:** Cross-model consensus verification. Disagreements with A are logged and force explicit judge resolution.

---

### Agent B — Vulnerability Analyst
**File:** `agents/vuln_agent.py`  
**Provider:** Mistral-Nemo (12B)  
**Prompt:** `prompts/prompt_b.txt`

**Output format:**
```
CVE STATUS: <CVE-YYYY-NNNNN or "No known CVE">
MITRE ATT&CK TACTIC: <e.g., Initial Access>
MITRE ATT&CK TECHNIQUE ID: <e.g., T1566>
ATTACK CHAIN: <2–3 step progression>
AFFECTED SYSTEMS: <software/OS/services>
```

**Constraints:** Cannot classify, score severity, or suggest actions.

---

### Agent C — Impact Assessor (Primary)
**File:** `agents/impact_agent.py`  
**Provider:** DeepSeek-R1  
**Prompt:** `prompts/prompt_c.txt`

**Output format:**
```
SEVERITY SCORE: <1–10>
  1–3: Low (minor, reversible)
  4–6: Medium (significant disruption)
  7–9: High (breach, financial/regulatory impact)
  10:  Critical (national infrastructure)

AFFECTED SCOPE: <Individual | Small Team | Organization | Sector-Wide | National Infrastructure>
POTENTIAL IMPACT: <Data Loss | Financial Loss | Service Disruption | ...>
TOP 3 IMMEDIATE ACTIONS: (priority-ordered direct instructions)
```

**Constraints:** Cannot classify, reference CVEs/MITRE, or provide remediation plans.

---

### Agent C₂ — Impact Assessor (Consensus Secondary)
**File:** `agents/impact_agent_2.py`  
**Provider:** Qwen2.5 (7B)  
**Prompt:** Same as Agent C (`prompts/prompt_c.txt`)  
**Purpose:** Cross-model severity verification. Conflicts >2 points flagged in `disagreement_log.severity`.

---

### Agent D — Remediation Engineer
**File:** `agents/remediation_agent.py`  
**Provider:** Mistral-Nemo (12B)  
**Prompt:** `prompts/prompt_d.txt`

**Output format:**
```
PATCH / FIX: <specific technical remediation>
CONTAINMENT: <≤4 immediate steps, direct commands, within 30 min>
TOOLS TO DEPLOY: <named tools: CrowdStrike, Wireshark, Splunk, etc.>
LONG-TERM HARDENING: <≤5 steps, within 72 hours>
RECOVERY STEPS: <data restoration, verification, notification, evidence>
```

**Constraints:** Cannot classify, reference MITRE IDs, or score severity.

---

### Judge Agent — CISO Synthesizer
**File:** `agents/judge_agent.py`  
**Provider:** Qwen2.5-72B  
**Prompt:** `prompts/prompt_judge.txt`

**Method signature:**
```python
synthesize(threat, agent_outputs, disagreement_log=None, round_weights=None)
```

**Input context includes:**
- All 6 agent outputs, each labeled with agent name, provider, and weight tag (`[REVISED POSITION — higher trust]` or `[STABLE POSITION]`)
- Structured consensus section: explicit CONFLICT or AGREEMENT statement for classification and severity

**Output format:**
```
FINAL CLASSIFICATION: <one of 9 canonical labels — word-for-word>
FINAL CVE AND MITRE MAPPING: <confirm or correct Agent B>
FINAL SEVERITY: <1–10 with one-sentence rationale>
CONTRADICTION REPORT: <list all conflicts + resolutions, or "No contradictions">
FINAL RESPONSE PLAN: <priority-ordered numbered actions>
```

**Rules enforced by prompt:**
- No hedging ("it could be", "possibly")
- If A and A₂ agree → high confidence; if they disagree → must resolve with reasoning
- Must be actionable by a real SOC team within 5 minutes

---

## 4. Prompt Engineering

### Validator Prompt (`prompt_validator.txt`)
- Two-mode structure: MODE A (raw input) / MODE B (raw + answers)
- Maximum 3 questions, priority: attack vector → symptoms → affected systems
- Mode B always produces Pass — no third round of questions ever
- Forbidden: classification, CVEs, MITRE, remediation

### Classifier Prompt (`prompt_a.txt`)
- Forces exactly 3 fields: THREAT CATEGORY, CONFIDENCE SCORE, JUSTIFICATION
- 9 canonical labels defined in prompt (label set matches `LABEL_MAP` in evaluator)
- One-sentence justification must reference specific indicators from the input

### Vuln Analyst Prompt (`prompt_b.txt`)
- Forces exactly 5 fields: CVE STATUS, MITRE TACTIC, TECHNIQUE ID, ATTACK CHAIN, AFFECTED SYSTEMS
- Strict separation from classification and severity domains

### Impact Prompt (`prompt_c.txt`)
- Anchored severity scale (1–3 Low, 4–6 Medium, 7–9 High, 10 Critical)
- 7 impact categories defined explicitly
- Top 3 actions must be direct instructions ("Block the sender domain") not advice ("consider blocking")

### Remediation Prompt (`prompt_d.txt`)
- Time-bounded containment (30 min) and hardening (72 hr)
- Step counts capped (≤4 containment, ≤5 hardening)
- Specificity enforced: named tools, not generic ("CrowdStrike" not "an EDR solution")

### Judge Prompt (`prompt_judge.txt`)
- Orchestrator appends consensus analysis block dynamically (not in the static prompt file)
- CRITICAL CLASSIFICATION RULE: final label must be word-for-word from the 9-label set
- No hedging language permitted
- Contradiction report is mandatory output field

---

## 5. Orchestration

**File:** `council/orchestrator.py`  
**Class:** `CyberCouncil`

### Key Methods

| Method | Description |
|--------|-------------|
| `analyze_sync(threat, user_answers)` | Sync wrapper — safe for Flask, scripts, notebooks |
| `analyze(threat, user_answers)` | Full async pipeline |
| `_run_agents_parallel(threat_input, loop)` | Runs all 6 agents via `asyncio.gather()` |
| `_run_agents_sequential(threat_input, loop)` | Legacy fallback for ≤16GB GPU |

### Result Dict Schema

```python
{
    "status":           "analyzed" | "rejected" | "needs_clarification",
    "original_input":   str,
    "clean_threat":     str,          # validator-enriched
    "validation":       dict,
    "round1_outputs":   list[dict],   # 6 agent outputs
    "draft_report":     str,
    "round2_outputs":   list[dict],   # 6 agent outputs (with draft context)
    "final_report":     str,
    "disagreement_log": {
        "classification": {
            "agent_a_primary":   str | None,
            "agent_a_secondary": str | None,
            "disagree":          bool,
        },
        "severity": {
            "agent_c_primary":   int | None,
            "agent_c_secondary": int | None,
            "disagree":          bool,
        },
        "round_changes": {
            "<agent_name>": {"changed": bool, "weight": float}
        }
    }
}
```

### Thread Pool

- Single `ThreadPoolExecutor(max_workers=10)` per process, shared across all calls
- Each agent `.analyze()` call is a blocking I/O call (Ollama HTTP) submitted to the pool
- asyncio event loop + `run_in_executor` gives non-blocking parallel I/O

---

## 6. Provider Pattern

**File:** `config/agent_config.py`

All LLM assignments live in one file. Provider swap = one line change. No other files touched.

### Current Configuration

```python
from providers.llama_provider        import LlamaProvider
from providers.deepseek_r1_provider  import DeepSeekR1Provider
from providers.mistral_nemo_provider import MistralNemoProvider
from providers.qwen2_5_provider      import Qwen25Provider

AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=800)
AGENT_A_PROVIDER         = DeepSeekR1Provider()    # Classifier (primary)
AGENT_A_2_PROVIDER       = Qwen25Provider()         # Classifier (consensus)
AGENT_B_PROVIDER         = MistralNemoProvider()    # Vuln Analyst
AGENT_C_PROVIDER         = DeepSeekR1Provider()     # Impact (primary)
AGENT_C_2_PROVIDER       = Qwen25Provider()         # Impact (consensus)
AGENT_D_PROVIDER         = MistralNemoProvider()    # Remediation
JUDGE_PROVIDER           = Qwen25Provider()         # Judge/CISO (72B)
```

All providers implement `BaseLLMProvider`:
```python
def complete(self, system_prompt: str, user_message: str) -> str: ...
def provider_name(self) -> str: ...
```

Provider name is logged in every agent output — enables cross-model ablation traceability in paper tables.

### Available Providers

| Provider | File | Backend | Models |
|----------|------|---------|--------|
| `LlamaProvider` | `providers/llama_provider.py` | Ollama HTTP | llama3, gemma2, mistral, etc. |
| `DeepSeekR1Provider` | `providers/deepseek_r1_provider.py` | Ollama HTTP | deepseek-r1 |
| `MistralNemoProvider` | `providers/mistral_nemo_provider.py` | Ollama HTTP | mistral-nemo |
| `Qwen25Provider` | `providers/qwen2_5_provider.py` | Ollama HTTP | qwen2.5 (7B and 72B) |
| `ClaudeProvider` | `providers/claude_provider.py` | Anthropic API | claude-sonnet-4-6, claude-opus-4-6 |
| `OpenAIProvider` | `providers/openai_provider.py` | OpenAI API | gpt-4o, gpt-4-turbo |

---

## 7. Evaluation Framework

### Dataset

| File | Samples | Purpose |
|------|---------|---------|
| `data/sample_threats.json` | 10 | Quick smoke tests, richness evaluation |
| `data/threats.json` | 50 | Full evaluation and baselines |

Generated by `scripts/build_dataset.py`. Format:
```json
[{"id": 1, "threat_description": "...", "true_label": "Phishing"}, ...]
```

### Metrics (`evaluation/metrics.py`)

- Accuracy, Precision (macro), Recall (macro), F1 (macro) — via sklearn
- Label extraction: scans judge final report for canonical label strings; defaults to "Other" if none found

### Evaluation Systems

| System | Description | Script |
|--------|-------------|--------|
| Full Council + Judge | 6 agents × 2 rounds + judge | `run_eval.py` |
| Baseline 1 — Single Agent | Agent A provider with minimal prompt, no council | `run_baselines.py` |
| Baseline 2 — Majority Vote | 3× ClassifierAgent runs, majority vote, no judge | `run_baselines.py` |

### Richness Evaluation (`evaluation/richness_evaluator.py`)

Scores each system's output on 5 dimensions:

| Dimension | Single Agent | Full Council |
|-----------|-------------|-------------|
| Threat classified | 1.0 | 1.0 |
| MITRE ATT&CK mapped | 0.0 | ~1.0 |
| Severity scored | 0.0 | ~1.0 |
| Response plan present | 0.0 | ~1.0 |
| Contradiction addressed | 0.0 | ~1.0 |
| **Total (out of 5)** | **1.0** | **~5.0** |

### Output Files (`results/`)

| File | Contents |
|------|----------|
| `eval_results.json` | Classification metrics, richness comparison, `disagreement_stats` block |
| `eval_cache.json` | Per-sample results cache with full `disagreement_log` per item |
| `baseline_results.json` | Baseline 1 & 2 metrics + per-sample predictions |
| `samples/sample_NNN.txt` | Full per-sample report: inputs, all agent outputs, judge reports, consensus log |
| `*_confusion.png` | Confusion matrix heatmaps |
| `*_metrics_bar.png` | Accuracy/Precision/Recall/F1 bar charts |
| `comparison_chart.png` | Side-by-side system comparison |

### `disagreement_stats` in `eval_results.json`

```json
"disagreement_stats": {
    "classification_conflicts": 12,
    "severity_conflicts":       8,
    "total_agent_revisions":    31,
    "samples_evaluated":        50
}
```

Directly usable in paper tables to demonstrate the council's conflict detection and resolution activity.

---

## 8. Caching & Resumable Runs

**File:** `evaluation/cache.py`

- Results cached per-item to `results/eval_cache.json` immediately after completion
- If run crashes, restart resumes from the crash point — no re-processing of completed items
- `invalidate_stale_items(cache_data, required_keys)` — auto-evicts items missing schema keys (e.g., after adding `disagreement_log`)
- `run_eval.py` calls this on startup to evict pre-disagreement-log cache entries

```bash
python3 run_eval.py              # resumes from cache
python3 run_eval.py --clear-cache  # full fresh run
```

---

## 9. Web UI

**File:** `server.py`  
**Port:** `http://127.0.0.1:5050`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Run full council analysis. Returns `disagreement_log` in response. |
| `/api/health` | GET | Check Ollama connectivity + list loaded models |
| `/api/config` | GET | Return all 8 provider names (validator, A, A₂, B, C, C₂, D, judge) |

### `/api/analyze` Response

```json
{
    "status":           "analyzed",
    "clean_threat":     "...",
    "round1_outputs":   [...],
    "draft_report":     "...",
    "round2_outputs":   [...],
    "final_report":     "...",
    "disagreement_log": {...},
    "elapsed_sec":      7.4
}
```

---

## 10. Performance Profile

**Hardware:** RTX 5060 Ti (16GB VRAM + 18GB shared = 34GB), Intel Core Ultra 9, 32GB RAM

| Phase | Time | Memory |
|-------|------|--------|
| Validator (Llama-3 8B) | 2–3 sec | ~4 GB |
| 6 agents in parallel | 3–5 sec (wall) | ~22 GB peak |
| Judge (Qwen2.5-72B) | 3–5 sec | ~37 GB (uses shared RAM) |
| **Per-threat total** | **5–10 sec** | **~37 GB peak** |
| 50-threat evaluation | ~5–10 min | — |

**Parallelism:** `asyncio.gather()` with `ThreadPoolExecutor(max_workers=10)` — 6 Ollama HTTP calls in parallel via non-blocking I/O.

---

## 11. Hardware & Software Requirements

### Hardware

| Component | Spec | Role |
|-----------|------|------|
| GPU | RTX 5060 Ti, 16GB VRAM | Agent inference |
| Shared GPU memory | 18GB from system RAM | Judge (Qwen 72B) overflow |
| System RAM | 32GB | OS + shared GPU memory |
| Disk | 954GB | Model storage (~45GB for all models) |

### Software

| Package | Purpose |
|---------|---------|
| Ollama | Local LLM inference server |
| Python 3.10+ | Runtime |
| anthropic | Claude API (optional) |
| openai | GPT API (optional) |
| flask + flask-cors | Web UI server |
| scikit-learn | Evaluation metrics |
| tqdm | Evaluation progress bars |
| matplotlib | Chart generation |
| python-dotenv | API key management |

### Model Pull Commands

```bash
ollama pull llama3        # Validator — 8B
ollama pull deepseek-r1   # Agent A, C — reasoning
ollama pull mistral-nemo  # Agent B, D — technical
ollama pull qwen2.5       # Agent A₂, C₂, Judge — 7B + 72B variants
```

---

## 12. Ablation Studies

### What to Vary

| Ablation | How |
|----------|-----|
| Judge vs. no judge | Replace judge with majority vote (edit `run_eval.py`) |
| Consensus pairs vs. single | Remove A₂, C₂ from `CyberCouncil.agents` in orchestrator |
| Round 2 vs. single pass | Skip Round 2, use Round 1 final report as judge input |
| Round-change weighting vs. flat | Pass `round_weights=None` to judge `synthesize()` |
| Provider swap | Edit `config/agent_config.py` — zero code changes |

### Paper Comparison Table Template

| Configuration | Accuracy | Precision | Recall | F1 |
|---------------|----------|-----------|--------|-----|
| Single Agent (Baseline 1) | — | — | — | — |
| Council, No Judge (Baseline 2) | — | — | — | — |
| Full Council + Judge | — | — | — | — |
| Council, No Consensus Pairs | — | — | — | — |
| Council, No Round 2 | — | — | — | — |

Run each configuration, copy from `eval_results.json`.

---

## 13. Reproducibility

All components are deterministic given the same models:
- Prompts version-controlled in `prompts/`
- Provider assignments explicit in `config/agent_config.py`
- Dataset labels fixed in `data/threats.json`
- Per-sample results + disagreement logs cached in `results/eval_cache.json`
- Charts and CSVs auto-generated to `results/`

**Reproduction steps:**
```bash
git clone <repo>
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
ollama pull llama3 deepseek-r1 mistral-nemo qwen2.5
python3 scripts/build_dataset.py
python3 run_eval.py
python3 run_baselines.py
```

---

## 14. Key Design Principles

1. **Config-Driven Assembly** — All provider-to-agent wiring in one file. Zero code changes for LLM swaps.
2. **Prompts as Files** — All prompts in `.txt` files. Iterate without touching Python.
3. **Provider Transparency** — Every agent output includes provider name. Judge knows model provenance.
4. **Strict Agent Boundaries** — Each agent has a defined scope. Judge resolves scope conflicts.
5. **Disagreement as Signal** — Cross-model conflicts are not failures — they are logged and used to strengthen judge arbitration.
6. **Revision as Signal** — Round 2 position changes indicate active reasoning. Weighted 1.5× vs. stable outputs.
7. **Open/Closed Principle** — Add providers with one new file + one config line. No orchestrator changes.

---

## 15. File Reference

```
cyberPaper/
├── main.py                        # Single threat test (prints disagreement log)
├── server.py                      # Flask API + SOC web UI
├── run_eval.py                    # Full evaluation + disagreement stats
├── run_baselines.py               # Baseline 1 & 2 comparison
│
├── agents/
│   ├── base_agent.py
│   ├── validator_agent.py         # Agent 0
│   ├── classifier_agent.py        # Agent A (primary)
│   ├── classifier_agent_2.py      # Agent A₂ (consensus)
│   ├── vuln_agent.py              # Agent B
│   ├── impact_agent.py            # Agent C (primary)
│   ├── impact_agent_2.py          # Agent C₂ (consensus)
│   ├── remediation_agent.py       # Agent D
│   └── judge_agent.py             # Judge (synthesize + disagreement resolution)
│
├── providers/
│   ├── base_provider.py
│   ├── llama_provider.py
│   ├── deepseek_r1_provider.py
│   ├── mistral_nemo_provider.py
│   ├── qwen2_5_provider.py
│   ├── claude_provider.py
│   └── openai_provider.py
│
├── prompts/
│   ├── prompt_validator.txt       # Validator (2-pass, attack vector priority)
│   ├── prompt_a.txt               # Classifier (9 labels, confidence, justification)
│   ├── prompt_b.txt               # Vuln Analyst (CVE, MITRE, attack chain)
│   ├── prompt_c.txt               # Impact (severity 1–10, scope, actions)
│   ├── prompt_d.txt               # Remediation (patch, containment, hardening)
│   └── prompt_judge.txt           # Judge (synthesis, contradiction, response plan)
│
├── config/
│   └── agent_config.py            # All provider assignments (ONLY file to edit for LLM swaps)
│
├── council/
│   └── orchestrator.py            # CyberCouncil class (6-agent pipeline, disagreement detection)
│
├── evaluation/
│   ├── metrics.py                 # compute_metrics()
│   ├── evaluator.py               # run_evaluation(), run_baseline2_majority_vote()
│   ├── baselines.py               # run_single_agent_baseline(), run_majority_vote_baseline()
│   ├── richness_evaluator.py      # run_richness_comparison()
│   ├── cache.py                   # load/save/invalidate cache
│   └── reporter.py                # save_report(), save_comparison_chart()
│
├── data/
│   ├── sample_threats.json        # 10 samples (smoke tests)
│   └── threats.json               # 50 samples (full eval)
│
├── scripts/
│   └── build_dataset.py           # Generate 50-sample dataset
│
├── results/                       # Auto-generated outputs
│   ├── eval_results.json
│   ├── eval_cache.json
│   ├── baseline_results.json
│   ├── samples/sample_NNN.txt
│   └── *.png, *.csv
│
└── frontend/                      # SOC dark-theme web UI
```
