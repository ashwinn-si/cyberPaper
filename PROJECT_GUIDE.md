# CyberCouncil — Complete Project Guide

## Overview

**CyberCouncil** is a multi-agent LLM system for cybersecurity threat detection, classification, and response synthesis. Designed for IEEE research publication.

**Core Innovation:** Multi-agent consensus + Judge arbitration improves threat classification accuracy. Extensible provider pattern allows mixing Claude, GPT-4, and future LLMs per agent with zero code changes.

---

## System Flow

```
Raw Threat Input
    ↓
┌─────────────────────────────────────┐
│  Agent 0: Validator                 │ → validates input, asks clarifying questions, enriches threat
│  (Pass 1 & 2 if needed)             │
└────────────┬────────────────────────┘
             │ Enriched threat
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   ROUND 1 (parallel)                             │
│   Agent A:  Threat Classifier (primary)    ──┐                  │
│   Agent A₂: Threat Classifier (consensus)  ──┤                  │
│   Agent B:  Vulnerability Analyst          ──┼─→ asyncio.gather │
│   Agent C:  Impact Assessor (primary)      ──┤                  │
│   Agent C₂: Impact Assessor (consensus)   ──┤                  │
│   Agent D:  Remediation Engineer           ──┘                  │
└─────────────────┬────────────────────────────────────────────────┘
                  │ 6 agent outputs
                  ▼
    Disagreement detection (A vs A₂, C vs C₂)
    → disagreement_log built
                  │
                  ▼
         Judge: Round 1 synthesis + disagreement_log
             (draft report)
                  │
                  ▼
┌──────────────────────────────────────────────────────────────────┐
│              ROUND 2 (parallel, sees draft)                      │
│   All 6 agents re-analyze with draft context                     │
└─────────────────┬────────────────────────────────────────────────┘
                  │ 6 agent outputs (refined)
                  ▼
    Round-change weighting (revised agents → weight 1.5)
                  │
                  ▼
     Judge: Round 2 synthesis + weights + disagreement_log
         (final SOC-ready report)
```

---

## Directory Structure

```
cyberPaper/
├── agents/                    # Agent implementations
│   ├── base_agent.py            # Abstract BaseAgent class
│   ├── validator_agent.py       # Agent 0 — input validation (pass_one, pass_two)
│   ├── classifier_agent.py      # Agent A — threat classification (primary)
│   ├── classifier_agent_2.py    # Agent A₂ — threat classification (consensus)
│   ├── vuln_agent.py            # Agent B — CVE + MITRE mapping
│   ├── impact_agent.py          # Agent C — severity scoring (primary)
│   ├── impact_agent_2.py        # Agent C₂ — severity scoring (consensus)
│   ├── remediation_agent.py     # Agent D — remediation prescription
│   └── judge_agent.py           # Judge — synthesis, disagreement resolution & arbitration
│
├── providers/                 # LLM Provider abstraction
│   ├── base_provider.py      # Abstract BaseLLMProvider
│   ├── claude_provider.py    # Claude (Anthropic)
│   ├── openai_provider.py    # GPT-4 (OpenAI)
│   └── llama_provider.py     # Llama 3 (local endpoint)
│
├── prompts/                   # System prompts (editable, no code changes)
│   ├── prompt_validator.txt  # Agent 0 — MODE A/B validation logic
│   ├── prompt_a.txt          # Agent A — threat classification spec
│   ├── prompt_b.txt          # Agent B — CVE/MITRE spec
│   ├── prompt_c.txt          # Agent C — impact scoring spec
│   ├── prompt_d.txt          # Agent D — remediation steps
│   └── prompt_judge.txt      # Judge — synthesis & contradiction resolution
│
├── council/                   # Orchestration
│   └── orchestrator.py       # CyberCouncil class — parallel execution + 2-round flow
│
├── config/                    # Configuration
│   └── agent_config.py       # Provider assignment (ONLY file to edit for LLM swaps)
│
├── evaluation/                # Evaluation & metrics
│   ├── evaluator.py          # run_evaluation() — full dataset analysis
│   ├── metrics.py            # compute_metrics() — accuracy, precision, recall, F1
│   ├── baselines.py          # baseline implementations (single agent, majority vote)
│   └── reporter.py           # save results to CSV/PNG/JSON
│
├── frontend/                  # Web UI
│   └── app.js                # Dark-theme SOC dashboard
│
├── scripts/                   # Utilities
│   └── build_dataset.py      # Generate threat dataset from descriptions
│
├── tests/                     # Testing
│   └── test_local.py         # Local test runner (4 scenarios)
│
├── data/                      # Datasets
│   ├── sample_threats.json   # 10 samples (quick testing)
│   └── threats.json          # 50 full dataset (generated)
│
├── results/                   # Evaluation outputs
│   ├── eval_results.json
│   ├── council_metrics.csv
│   ├── council_predictions.csv
│   ├── council_confusion.png
│   ├── council_metrics_bar.png
│   └── comparison_chart.png
│
├── main.py                    # Single threat test (edit threat var, run)
├── server.py                  # Flask web UI (run, open http://127.0.0.1:5050)
├── run_eval.py               # Full evaluation on dataset
├── run_baselines.py          # Baseline comparisons
│
├── CLAUDE.md                  # Project instructions (in git, read first!)
├── PROJECT_GUIDE.md           # This file
├── requirements.txt           # Dependencies
├── .env.example              # API key template
└── .gitignore                # Exclude .env, results/, __pycache__/
```

---

## Core Concepts

### 1. Provider Pattern (Extensibility)

**Problem:** Research requires testing different LLMs (Claude, GPT-4, Gemini, Llama).  
**Solution:** Abstract provider interface + single config file.

**All LLM assignment happens in ONE file:**

```python
# config/agent_config.py
from providers.claude_provider import ClaudeProvider
from providers.openai_provider import OpenAIProvider

AGENT_A_PROVIDER         = ClaudeProvider()        # Threat Classifier
AGENT_B_PROVIDER         = ClaudeProvider()        # Vuln Analyst
AGENT_C_PROVIDER         = ClaudeProvider()        # Impact Assessor
AGENT_D_PROVIDER         = ClaudeProvider()        # Remediation
AGENT_VALIDATOR_PROVIDER = ClaudeProvider()        # Validator
JUDGE_PROVIDER           = ClaudeProvider()        # Judge
```

**To swap models:**

```python
# All GPT-4o
AGENT_A_PROVIDER = OpenAIProvider("gpt-4o")
AGENT_B_PROVIDER = OpenAIProvider("gpt-4o")
AGENT_C_PROVIDER = OpenAIProvider("gpt-4o")
AGENT_D_PROVIDER = OpenAIProvider("gpt-4o")
JUDGE_PROVIDER   = OpenAIProvider("gpt-4o")

# Or mix
AGENT_A_PROVIDER = ClaudeProvider("claude-opus-4-6")
AGENT_B_PROVIDER = OpenAIProvider("gpt-4o")
JUDGE_PROVIDER   = ClaudeProvider("claude-sonnet-4-6")
```

**Why this matters for the paper:**

- Provider names logged in every agent output → reproducibility
- Enables ablation studies (single agent vs. council, different model combinations)
- Zero code changes required — extensible design principle

---

### 2. Agent Specifications

| Agent                    | File                      | Provider         | Output                                         | Constraints                              |
| ------------------------ | ------------------------- | ---------------- | ---------------------------------------------- | ---------------------------------------- |
| **0 — Validator**        | `validator_agent.py`      | Llama-3          | Pass / Needs Clarification / Invalid           | None                                     |
| **A — Classifier**       | `classifier_agent.py`     | DeepSeek-R1      | Threat category + confidence %                 | No CVEs, MITRE, impacts                  |
| **A₂ — Classifier-2**   | `classifier_agent_2.py`   | Qwen2.5 7B       | Threat category + confidence % (consensus)     | Same as A — cross-model verification     |
| **B — Vuln Analyst**     | `vuln_agent.py`           | Mistral-Nemo     | CVE ID, MITRE ATT&CK tactic/technique          | No classification, severity, actions     |
| **C — Impact Assessor**  | `impact_agent.py`         | DeepSeek-R1      | Severity 1–10, affected scope, impacts         | No classification, CVEs, MITRE           |
| **C₂ — Impact-2**        | `impact_agent_2.py`       | Qwen2.5 7B       | Severity 1–10, affected scope (consensus)      | Same as C — cross-model verification     |
| **D — Remediation**      | `remediation_agent.py`    | Mistral-Nemo     | Patch, containment, tools, hardening, recovery | No classification, MITRE, severity       |
| **Judge (CISO)**         | `judge_agent.py`          | Qwen2.5-72B      | Final actionable report                        | Must synthesize + resolve contradictions |

**Design:** Strict boundaries force specialization. A₂/C₂ pairs enable cross-model consensus. Judge receives disagreement_log and resolves conflicts explicitly.

---

### 3. Validation Pipeline (Agent 0)

**Mode A — First Pass (raw input):**

- Evaluates input for relevance, specificity, clarity
- Returns one of three responses:
  1. **Invalid** — not a security threat, reject with explanation
  2. **Needs Clarification** — security-related but vague, ask up to 3 questions
  3. **Pass** — sufficient detail, enrich and proceed

**Mode B — Second Pass (original + user answers):**

- Always produces Pass (no more questions)
- Merges original input + answers into clean threat description

**Example flow:**

```
User: "my computer is acting weird"
    → Agent 0 Pass 1: "Needs Clarification"
       Q1: What started after?
       Q2: What symptoms?
       Q3: Which systems?
User answers: "After email attachment. Popups + loud fan. Just my laptop."
    → Agent 0 Pass 2: "Pass"
       Enriched: "An employee's Windows laptop exhibits signs of malware infection..."
       ↓ (agents A-D analyze this cleaned threat)
```

---

### 4. Parallel Execution (Round 1 & 2)

**Old:** Sequential agents → 4 × latency  
**New:** `asyncio.gather()` → 1 × latency per round

Each agent's blocking API call runs in its own thread via `ThreadPoolExecutor(max_workers=8)`.

```python
# In council/orchestrator.py
async def _run_agents_parallel(self, threat_input: str, loop) -> list:
    tasks = [
        loop.run_in_executor(_EXECUTOR, agent.analyze, threat_input)
        for agent in self.agents
    ]
    return list(await asyncio.gather(*tasks))
```

**Wall-clock time savings:**

- Round 1: 4 agents in parallel + Judge = `agent_latency + judge_latency`
- Round 2: 4 agents in parallel + Judge = `agent_latency + judge_latency`
- **Total:** ~2 × latency (vs. sequential: ~10 × latency)

---

### 5. Two-Round Judge Synthesis

**Round 1:** Judge reads all 4 agent outputs → drafts report with contradictions noted

**Round 2:** Agents see the draft and re-analyze with that context. Judge synthesizes refined outputs → final report

**Why two rounds?**

- Round 1 flags conflicts
- Round 2 allows agents to reconsider with peer feedback
- Final report is more nuanced, less contradictory

---

## How to Run

### 0. Initial Setup (One-time)

```bash
# Navigate to project directory
cd cyberPaper

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Mac/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 1. Install Dependencies

```bash
# Make sure you're in the activated environment (venv)
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy template
cp .env.example .env

# Edit .env with your API keys
# For Llama: set LLAMA_API_BASE and LLAMA_MODEL
# For Claude: set ANTHROPIC_API_KEY
# For GPT-4: set OPENAI_API_KEY
```

---

### 3. Generate Dataset (if needed)

```bash
python3 scripts/build_dataset.py
```

This generates the full **50-sample threat dataset** used for evaluation. Outputs to `data/threats.json`.

**Already included:** `data/sample_threats.json` (10 quick samples for testing)

For custom output path:
```bash
python3 scripts/build_dataset.py --out data/custom_threats.json
```

---

### Running Tests (with activated environment)

**All commands below assume you've activated the venv:**

```bash
source venv/bin/activate  # (or venv\Scripts\activate on Windows)
```

#### Local Test (4 scenarios) — Start here

```bash
python3 tests/test_local.py
```

Tests all paths:

1. Clear threat (straight through)
2. Vague threat (with user answers supplied)
3. Invalid input (rejected)
4. Phishing attack (parallel agents stress test)

**Expected output:** All 4 test cases pass with agent outputs visible.

---

#### Single Threat Test

```bash
python3 main.py
```

Edit the `threat` variable in `main.py` to test different scenarios. Runs a single threat through the full council + judge pipeline.

---

#### Web UI (Interactive)

```bash
python3 server.py
```

Then open browser: **http://127.0.0.1:5050**

Dark-theme SOC dashboard. Submit threats interactively, see full analysis and final report.

---

#### Full Evaluation (50-sample dataset)

```bash
python3 run_eval.py
```

Runs all 50 threats through the full council + judge pipeline. Outputs to `results/`:

- `eval_results.json` — raw metrics (accuracy, precision, recall, F1)
- `council_metrics.csv` — per-class breakdown
- `council_predictions.csv` — true vs. predicted labels
- `council_confusion.png` — confusion matrix heatmap (grayscale, paper-ready)
- `council_metrics_bar.png` — metric bars by class (grayscale, paper-ready)

**Time:** ~5–10 min depending on API latency.

---

#### Baseline Comparisons

```bash
python3 run_baselines.py
```

Compares:

1. **Baseline 1:** Single Agent A only (no council)
2. **Baseline 2:** Majority vote of A, B, C (no judge)
3. **Full System:** All agents + Judge (full council)

**Outputs:** `results/comparison_chart.png` (grayscale, paper-ready)

**Time:** ~3–5 min.

---

### Recommended Test Sequence

0. **Entering the environment**

```bash
source venv/bin/activate
```

1. **Local test first** (validate setup):

   ```bash
   python3 tests/test_local.py
   ```

   Should complete in ~1–2 min. If all pass, environment is ready.

2. **Single threat** (verify main flow):

   ```bash
   python3 main.py
   ```

3. **Generate dataset** (50-sample dataset for evaluation):

   ```bash
   python3 scripts/build_dataset.py
   ```

   Generates `data/threats.json` (50 labeled threats across 9 categories).

4. **Full evaluation** (comprehensive results for paper):

   ```bash
   python3 run_eval.py
   ```

   Outputs to `results/`:
   - CSV metrics + predictions
   - Grayscale confusion matrix + metric bars (paper-ready)

5. **Baselines** (comparative analysis):

   ```bash
   python3 run_baselines.py
   ```

   Compares single agent vs. majority vote vs. full council+judge.

---

## For the IEEE Paper

### Required Sections

1. **System Architecture** — reference the flow diagram above
2. **Provider Pattern Design** — explain extensibility novelty
3. **Agent Prompts** — quote key rules (no hedging, strict boundaries)
4. **Experimental Setup** — dataset, baselines, ablations
5. **Results Table** — accuracy/precision/recall/F1 for all configurations
6. **Ablation Study** — prove each agent + Judge contributes to accuracy

### Reproducibility Checklist

- [ ] All prompt text in `prompts/` is version-controlled
- [ ] Provider configurations in `config/agent_config.py` are explicit
- [ ] Dataset labels fixed in `data/`
- [ ] Results (CSV, PNG, JSON) auto-generated and saved
- [ ] `.env` NOT committed (use `.env.example` as template)
- [ ] All experiments logged with provider names in outputs

### Key Claims to Demonstrate

1. **Multi-agent consensus improves accuracy**  
   Compare: Single agent vs. Full council (baseline vs. full system)

2. **Judge arbitration resolves conflicts**  
   Show: Contradiction report examples, final accuracy gain

3. **Provider swapping requires zero code changes**  
   Document: Update `config/agent_config.py`, rerun — done

4. **Each agent independently contributes**  
   Ablation study: Remove one agent, measure accuracy drop

---

## Adding a New Provider

To support Gemini, Mistral, or any LLM:

### Step 1: Create `providers/gemini_provider.py`

```python
import os
import google.generativeai as genai
from providers.base_provider import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gemini-pro"):
        self.model_name = model_name
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model_name)

    def complete(self, system_prompt: str, user_message: str) -> str:
        response = self.model.generate_content(f"{system_prompt}\n\n{user_message}")
        return response.text

    def provider_name(self) -> str:
        return f"Gemini ({self.model_name})"
```

### Step 2: Update `config/agent_config.py`

```python
from providers.gemini_provider import GeminiProvider

AGENT_A_PROVIDER = GeminiProvider()  # ✓ Done
```

**That's it.** No other files need to change.

---

## Environment Setup

```bash
# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# API keys
cp .env.example .env
# Edit .env with ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.
```

---

## Key Design Principles

1. **Config-Driven Assembly**  
   All provider-to-agent wiring in `config/agent_config.py`

2. **Prompts as Files**  
   System prompts in `prompts/` — iterate without code changes

3. **Provider Transparency**  
   Every output includes provider name (e.g., "Claude (sonnet-4-6)")

4. **Strict Agent Boundaries**  
   Each agent has defined scope — Judge resolves conflicts

5. **Open/Closed Principle**  
   Agents closed to modification, open to extension (new providers)

6. **Two-Round Synthesis**  
   Agents re-analyze with peer feedback → nuanced final report

7. **Parallel Execution**  
   asyncio + ThreadPoolExecutor → 3–4x speedup over sequential

---

## Important Notes

- **API Keys:** Keep `.env` secure. Never commit. Use `.env.example` as template.
- **Rate Limits:** 50 samples × 4 agents × 2 rounds + Judge ≈ 450+ API calls. Budget accordingly.
- **Default Model:** Claude Sonnet 4. Opus is more capable but slower/costlier. Change in `config/agent_config.py`.
- **Label Mapping:** Threat labels must match categories in `evaluation/evaluator.py` `LABEL_MAP`.

---

## Related Files

- `.env.example` — API key template
- `requirements.txt` — dependencies (anthropic, openai, flask, sklearn, etc.)
- `.gitignore` — excludes `.env`, `results/`, `__pycache__/`
- `CLAUDE.md` — detailed project instructions
