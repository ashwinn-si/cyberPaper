# CyberCouncil — Project Instructions

> ⚠️ **ALWAYS read this file BEFORE starting work on this project.** It contains essential context about the architecture, how to run experiments, and how to use the code-review-graph tools.

---

## 📋 Project Overview

**CyberCouncil** is a multi-agent LLM system for cybersecurity threat detection and analysis, designed for IEEE research publication.

- **Architecture:** 3 specialized agents analyze threats independently, then a Judge agent synthesizes them into a final report
- **Goal:** Demonstrate that multi-agent consensus with judge arbitration improves threat classification accuracy
- **Novel contribution:** Extensible provider pattern allows mixing Claude, GPT-4, and future LLMs per agent with zero code changes

---

## 🏗️ System Architecture

### The Council Flow

```
Threat Input
    ↓
┌─────────────────────────────────────┐
│  Agent A: Threat Classifier         │ → classifies threat type
│  Agent B: Vulnerability Analyst     │ → maps to CVE + MITRE ATT&CK
│  Agent C: Impact Assessor           │ → scores severity + actions
└─────────────────────────────────────┘
    ↓
    Judge Agent (CISO role)
    → synthesizes all 3 outputs
    → resolves contradictions
    → produces final actionable report
```

### Layer Structure

| Layer | Files | Purpose |
|-------|-------|---------|
| **Providers** | `providers/*.py` | Abstract LLM interface (Claude/GPT/Gemini) |
| **Config** | `config/agent_config.py` | **Only file to edit** for provider swaps |
| **Agents** | `agents/*.py` | Threat analysis specialists + judge |
| **Prompts** | `prompts/prompt_*.txt` | System prompts (can iterate without code changes) |
| **Council** | `council/orchestrator.py` | Orchestrates all agents + judge |
| **Evaluation** | `evaluation/*.py` | Metrics, baselines, dataset loading |
| **Frontend** | `server.py` + `frontend/` | Flask API + dark-theme SOC UI |

---

## 🚀 Quick Start

### 0. Before You Begin
**Read this file** — it contains architecture overview, layer structure, and how to use code-review-graph tools.

For codebase exploration, **use the code-review-graph tools FIRST** (see section below). They're faster and cheaper than manual Grep/Read.

### 1. Environment Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and fill in API keys
cp .env.example .env
# Edit .env with ANTHROPIC_API_KEY and/or OPENAI_API_KEY
```

### 2. Test a Single Threat
```bash
python3 main.py
```
Edit the `threat` string in `main.py` to test different scenarios.

### 3. Run Web UI
```bash
python3 server.py
# Open http://127.0.0.1:5050
```

---

## 🔧 Using code-review-graph for Codebase Exploration

**This project has a knowledge graph. Always use these tools BEFORE Grep/Glob/Read** — they're faster, cheaper, and give you structural context.

### When to use graph tools FIRST

| Task | Tool |
|------|------|
| **Exploring code** | `semantic_search_nodes` or `query_graph` |
| **Understanding impact** | `get_impact_radius` (instead of manual tracing) |
| **Code review** | `detect_changes` + `get_review_context` |
| **Tracing relationships** | `query_graph` (callers_of, callees_of, imports_of, tests_for) |
| **Architecture overview** | `get_architecture_overview` + `list_communities` |
| **Finding functions/classes** | `semantic_search_nodes` (by name or keyword) |

### Example Workflow

1. **Exploring a new area:** `semantic_search_nodes` query="agent" → get all agent-related code
2. **Understanding impact of a change:** `get_impact_radius` on the file you modified
3. **Code review:** `detect_changes` on modified files, then `get_review_context` for snippets
4. **Finding tests:** `query_graph` pattern="tests_for" file="providers/claude_provider.py"

**Fall back to Grep/Glob/Read only when the graph doesn't have what you need.**

---

## 🔄 Provider Pattern (How to Swap LLMs)

**All provider assignment happens in ONE file: `config/agent_config.py`**

### Default Setup
```python
from providers.claude_provider import ClaudeProvider
from providers.openai_provider import OpenAIProvider

AGENT_A_PROVIDER = ClaudeProvider()         # Threat Classifier
AGENT_B_PROVIDER = ClaudeProvider()         # Vuln Analyst
AGENT_C_PROVIDER = ClaudeProvider()         # Impact Assessor
JUDGE_PROVIDER   = ClaudeProvider()         # Judge
```

### Swap Examples

**All GPT-4o:**
```python
AGENT_A_PROVIDER = OpenAIProvider()
AGENT_B_PROVIDER = OpenAIProvider()
AGENT_C_PROVIDER = OpenAIProvider()
JUDGE_PROVIDER   = OpenAIProvider()
```

**Mixed Models:**
```python
AGENT_A_PROVIDER = ClaudeProvider("claude-opus-4-6")
AGENT_B_PROVIDER = OpenAIProvider("gpt-4o")
AGENT_C_PROVIDER = OpenAIProvider("gpt-4-turbo")
JUDGE_PROVIDER   = ClaudeProvider("claude-sonnet-4-6")
```

**Why this matters for the paper:** Provider names are logged in every agent output, making ablation studies transparent and reproducible.

---

## 📊 Evaluation & Experiments

### Dataset
- Location: `data/sample_threats.json` (10 samples for testing)
- Full dataset: `data/threats.json` (50 samples, generated by `scripts/build_dataset.py`)
- Format: JSON array of `{id, threat_description, true_label}`

### Generate Dataset
```bash
python3 scripts/build_dataset.py
# or with custom path
python3 scripts/build_dataset.py --out data/custom_threats.json
```

### Run Full Evaluation
```bash
python3 run_eval.py
```
Outputs to `results/`:
- `eval_results.json` — raw metrics (accuracy, precision, recall, F1)
- `council_metrics.csv` — per-class breakdown
- `council_predictions.csv` — true vs predicted per sample
- `council_confusion.png` — confusion matrix heatmap
- `council_metrics_bar.png` — accuracy/precision/recall/F1 bar chart

### Run Baseline Comparisons
```bash
python3 run_baselines.py
```
Compares:
- Baseline 1: Single Agent A (no council)
- Baseline 2: Majority Vote (no judge)
- Full System: Council + Judge

Outputs comparison charts to `results/comparison_chart.png`.

### Ablation Study
For ablations (e.g., "council without judge"), modify `run_eval.py` to skip the judge and use majority vote instead. The framework is set up to make this trivial.

---

## 📝 Agent Specifications

### Agent A — Threat Classifier
**File:** `agents/classifier_agent.py` → loads `prompts/prompt_a.txt`  
**Output:** Category + Confidence % + Justification  
**Constraints:** Cannot discuss CVEs, impacts, or remediation

### Agent B — Vulnerability Analyst
**File:** `agents/vuln_agent.py` → loads `prompts/prompt_b.txt`  
**Output:** CVE ID + MITRE ATT&CK Tactic + Technique ID + Attack Chain + Affected Systems  
**Constraints:** Cannot classify, suggest actions, or score severity

### Agent C — Impact Assessor
**File:** `agents/impact_agent.py` → loads `prompts/prompt_c.txt`  
**Output:** Severity 1–10 + Affected Scope + Potential Impacts + Top 3 Immediate Actions  
**Constraints:** Cannot discuss classification, CVEs, or ATT&CK techniques

### Judge Agent — CISO Synthesizer
**File:** `agents/judge_agent.py` → loads `prompts/prompt_judge.txt`  
**Method:** `synthesize(threat, agent_outputs)` combines all 3 and produces final report  
**Output:** Final classification + CVE/MITRE + Severity + Contradiction Report + Response Plan  
**Key rule:** Must be decisive and usable by a real SOC team within 5 minutes

---

## 🔧 Adding a New Provider

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

AGENT_A_PROVIDER = GeminiProvider()  # ← done
```

**That's it.** No other files need to change. This is the core design principle of the system.

---

## 🎯 Key Design Principles

1. **Config-Driven Assembly**  
   All provider-to-agent wiring lives in one file (`config/agent_config.py`). Change the config, rerun — no code changes needed.

2. **Prompts as Files**  
   Prompts are `.txt` files, not hardcoded strings. Iterate on prompts without touching Python code. Commit prompt versions separately in git.

3. **Provider Transparency**  
   Every agent output includes the provider name (e.g., "Claude (claude-sonnet-4-6)"). The judge sees which model produced each analysis — useful for ablation studies.

4. **Strict Agent Boundaries**  
   Each agent has a defined scope (e.g., Agent A classifies but never scores severity). The judge resolves conflicts when agents disagree.

5. **Open/Closed Principle**  
   Agents are closed to modification, open to extension. Adding a new provider means one new file + one config line.

---

## 📂 File Reference

### Core Execution Flow
- `main.py` — single threat test (edit `threat` variable, run `python3 main.py`)
- `server.py` — Flask API + web UI (run `python3 server.py`, open http://127.0.0.1:5050)
- `run_eval.py` — full dataset evaluation
- `run_baselines.py` — baseline comparisons
- `scripts/build_dataset.py` — generate 50-sample dataset

### Provider Layer
- `providers/base_provider.py` — abstract `BaseLLMProvider` interface
- `providers/claude_provider.py` — Anthropic Claude implementation
- `providers/openai_provider.py` — OpenAI GPT implementation

### Agent Layer
- `agents/base_agent.py` — abstract `BaseAgent` class with `load_prompt()`
- `agents/classifier_agent.py` — Agent A
- `agents/vuln_agent.py` — Agent B
- `agents/impact_agent.py` — Agent C
- `agents/judge_agent.py` — Judge with `synthesize()` method

### System Prompts
- `prompts/prompt_a.txt` — Threat Classifier instructions
- `prompts/prompt_b.txt` — Vulnerability Analyst instructions
- `prompts/prompt_c.txt` — Impact Assessor instructions
- `prompts/prompt_judge.txt` — Judge/CISO instructions

### Orchestration
- `council/orchestrator.py` — `CyberCouncil` class that runs all agents + judge

### Evaluation
- `evaluation/metrics.py` — `compute_metrics()` using sklearn
- `evaluation/evaluator.py` — `run_evaluation()` function
- `evaluation/baselines.py` — baseline implementations

### Data & Results
- `data/sample_threats.json` — 10 test samples (for quick testing)
- `data/threats.json` — 50 full dataset (generated by `scripts/build_dataset.py`)
- `results/` — evaluation output directory (metrics, CSVs, charts)

---

## 📖 For the IEEE Paper

### Required Sections
1. **System Architecture** — reference the flow diagram above
2. **Provider Pattern Design** — explain why this extensibility is novel
3. **Agent Prompts** — quote the key rules (no hedging, strict boundaries)
4. **Experimental Setup** — dataset, baselines, ablations
5. **Results Table** — accuracy/precision/recall/F1 for all configurations
6. **Ablation Study** — prove each agent contributes to accuracy

### Reproducibility
- All prompt text in `prompts/` is version-controlled
- All provider configurations in `config/agent_config.py` are explicit
- Dataset labels are fixed in `data/`
- Results (CSV, PNG) are generated and saved automatically

### Key Claims
1. **Multi-agent consensus improves accuracy** — demonstrate with baselines
2. **Judge arbitration resolves agent conflicts** — show contradiction report examples
3. **Provider swapping requires no code changes** — document with examples
4. **Each agent independently contributes** — ablation study

---

## ⚠️ Important Notes

- **API Keys:** Keep `.env` secure. Never commit it. Use `.env.example` as template.
- **Rate Limits:** Running evaluation on 50 samples × 4 agents costs ~200 API calls. Budget accordingly.
- **Provider Models:** Default is Claude Sonnet 4. Opus is more capable but slower/costlier. Adjust in `config/agent_config.py`.
- **Label Mapping:** Threat labels must match categories in `evaluation/evaluator.py` `LABEL_MAP` or will default to "Other".

---

## 🔗 Related Files

- `.env.example` — template for API keys
- `requirements.txt` — dependencies (anthropic, openai, flask, sklearn, etc.)
- `.gitignore` — excludes `.env`, `results/`, `__pycache__/`
- `results/README.md` — empirical results analysis (if results exist)

---

## 💡 Getting Started: Before Your First Task

1. **Read this file** — you're reading it now ✓
2. **Run a basic test:** `python3 main.py` to verify environment
3. **Explore the codebase:** Use `semantic_search_nodes` or `query_graph` (see code-review-graph section above)
4. **Then execute your task** — whether it's a fix, feature, or experiment

## 📌 Standard Workflow for Any Task

1. **Read CLAUDE.md** (this file) for project context
2. **Use code-review-graph tools** to understand what you're modifying
   - `semantic_search_nodes` to find relevant code
   - `get_impact_radius` to understand what changes will affect
   - `query_graph` to trace callers/dependencies
3. **Use Grep/Glob/Read** only for small, targeted searches the graph doesn't cover
4. **Make your changes** with full context
5. **Use `detect_changes` + `get_review_context`** to review your work before committing

## 🔍 Quick Reference: When to Use What

| Need | Tool | Why |
|------|------|-----|
| Find all agent implementations | `semantic_search_nodes` | Indexes all code by function/class |
| Impact of changing a provider | `get_impact_radius` | Traces all dependents automatically |
| Review your code changes | `detect_changes` | Risk-scored, shows context |
| Find test coverage | `query_graph` pattern="tests_for" | Knows test relationships |
| Small targeted search | `Grep` | For specific strings/patterns |
| Manual file inspection | `Read` | Last resort when graph doesn't help |
