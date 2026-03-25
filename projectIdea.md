# CyberCouncil — Multi-Agent Threat Analysis System

> A multi-agent LLM council for cybersecurity threat detection, classification, and response synthesis.  
> Built for IEEE research publication. Designed with an extensible provider pattern — swap Claude ↔ GPT-4 per agent in one line.

---

## What This Project Does

This system sends a cybersecurity threat description to **3 specialized AI agents**. Each agent analyzes the threat from a different angle. A **Judge Agent** then reads all three outputs and produces a single authoritative final threat report.

Every agent is independently configurable — you can run Agent A on GPT-4, Agent B on Claude, and the Judge on either. No retraining, no code changes — just update `config/agent_config.py`.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Provider Layer                   │
│                                                         │
│   BaseLLMProvider (abstract)                            │
│       ├── ClaudeProvider     → Anthropic API            │
│       └── OpenAIProvider     → OpenAI API               │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    Agent Layer                          │
│                                                         │
│   BaseAgent (abstract)                                  │
│       ├── ClassifierAgent   (uses provider from config) │
│       ├── VulnAgent         (uses provider from config) │
│       ├── ImpactAgent       (uses provider from config) │
│       └── JudgeAgent        (uses provider from config) │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  Council Layer                          │
│                                                         │
│   CyberCouncil (orchestrator)                           │
│       → runs all agents → passes to judge → returns     │
│         final unified report                            │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
cybercouncil/
│
├── config/
│   └── agent_config.py          # ← SINGLE FILE to swap providers per agent
│
├── providers/
│   ├── __init__.py
│   ├── base_provider.py         # Abstract base — defines the interface
│   ├── claude_provider.py       # Anthropic Claude implementation
│   └── openai_provider.py       # OpenAI GPT implementation
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py            # Abstract base agent
│   ├── classifier_agent.py      # Agent A — threat classifier
│   ├── vuln_agent.py            # Agent B — CVE & MITRE analyst
│   ├── impact_agent.py          # Agent C — impact assessor
│   └── judge_agent.py           # Judge — final synthesizer
│
├── prompts/
│   ├── prompt_a.txt             # System prompt for Agent A
│   ├── prompt_b.txt             # System prompt for Agent B
│   ├── prompt_c.txt             # System prompt for Agent C
│   └── prompt_judge.txt         # System prompt for Judge
│
├── council/
│   ├── __init__.py
│   └── orchestrator.py          # Wires all agents into the council
│
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py               # Accuracy, Precision, Recall, F1
│   └── evaluator.py             # Runs dataset through council
│
├── data/
│   └── sample_threats.json      # Labeled threat dataset
│
├── results/
│   └── .gitkeep
│
├── main.py                      # Run one threat manually
├── run_eval.py                  # Full dataset evaluation
├── requirements.txt
└── .env                         # API keys (never commit this)
```

---

## The 4 Agents

| Agent                               | Role                                   | Output                                          |
| ----------------------------------- | -------------------------------------- | ----------------------------------------------- |
| **Agent A** — Threat Classifier     | Identifies the threat type             | Category + Confidence % + justification         |
| **Agent B** — Vulnerability Analyst | Maps CVE and MITRE ATT&CK              | CVE ID, ATT&CK tactic, technique ID             |
| **Agent C** — Impact Assessor       | Scores severity and recommends actions | Severity 1–10, impact types, top 3 actions      |
| **Judge**                           | Synthesizes all 3 reports              | Final unified report + contradiction resolution |

---

## Setup

```bash
git clone https://github.com/your-username/cybercouncil.git
cd cybercouncil
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

Create a `.env` file:

```
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
```

`requirements.txt`:

```
anthropic>=0.25.0
openai>=1.0.0
python-dotenv>=1.0.0
pandas>=2.0.0
scikit-learn>=1.3.0
numpy>=1.24.0
tqdm>=4.65.0
```

---

## Extensible Design — Provider Pattern (LLD)

The entire swap logic lives in **one file**: `config/agent_config.py`.  
The agents themselves never import Anthropic or OpenAI directly. They only talk to the abstract `BaseLLMProvider` interface. This means:

- Change a provider → edit one line in `config/agent_config.py`
- Add a new provider (Gemini, Mistral, etc.) → add one file in `providers/`
- No agent code ever needs to change

---

### `providers/base_provider.py` — The Interface

```python
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """
    Abstract interface for all LLM providers.
    Any new provider (Gemini, Mistral, etc.) must implement this.
    Agents only depend on this class — never on Claude or OpenAI directly.
    """

    @abstractmethod
    def complete(self, system_prompt: str, user_message: str) -> str:
        """
        Send a prompt to the LLM and return the text response.

        Args:
            system_prompt : The agent's role/persona instructions.
            user_message  : The actual threat or judge input.

        Returns:
            The LLM's response as a plain string.
        """
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """
        Return a human-readable label for logging.
        Example: 'Claude (claude-sonnet-4-20250514)' or 'OpenAI (gpt-4o)'
        """
        pass
```

---

### `providers/claude_provider.py` — Anthropic Claude

```python
import os
import anthropic
from dotenv import load_dotenv
from providers.base_provider import BaseLLMProvider

load_dotenv()

class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude provider.
    Default model : claude-sonnet-4-20250514
    Override model: ClaudeProvider("claude-opus-4-5")
    """

    def __init__(self, model_name: str = "claude-sonnet-4-20250514", max_tokens: int = 600):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def complete(self, system_prompt: str, user_message: str) -> str:
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text

    def provider_name(self) -> str:
        return f"Claude ({self.model_name})"
```

---

### `providers/openai_provider.py` — OpenAI GPT

```python
import os
from openai import OpenAI
from dotenv import load_dotenv
from providers.base_provider import BaseLLMProvider

load_dotenv()

class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI GPT provider.
    Default model : gpt-4o
    Override model: OpenAIProvider("gpt-4-turbo")
    """

    def __init__(self, model_name: str = "gpt-4o", max_tokens: int = 600):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def complete(self, system_prompt: str, user_message: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message}
            ]
        )
        return response.choices[0].message.content

    def provider_name(self) -> str:
        return f"OpenAI ({self.model_name})"
```

---

### `config/agent_config.py` — The Single Control File

**This is the only file you ever edit to swap providers.**  
Import what you need, assign to the constant — that is all.

```python
from providers.claude_provider import ClaudeProvider
from providers.openai_provider import OpenAIProvider

# ─────────────────────────────────────────────────────────────────
#  AGENT PROVIDER CONFIGURATION
#
#  Assign any provider to any agent independently.
#
#  Available options:
#    ClaudeProvider()                         Claude Sonnet (default)
#    ClaudeProvider("claude-opus-4-5")        Claude Opus
#    OpenAIProvider()                         GPT-4o (default)
#    OpenAIProvider("gpt-4-turbo")            GPT-4 Turbo
#
#  Change one line here. Nothing else in the codebase changes.
# ─────────────────────────────────────────────────────────────────

AGENT_A_PROVIDER = ClaudeProvider()       # Threat Classifier
AGENT_B_PROVIDER = ClaudeProvider()       # Vulnerability Analyst
AGENT_C_PROVIDER = ClaudeProvider()       # Impact Assessor
JUDGE_PROVIDER   = ClaudeProvider()       # Judge / Synthesizer
```

#### Swap example — GPT for all agents, Claude for judge only:

```python
AGENT_A_PROVIDER = OpenAIProvider()       # Threat Classifier     → GPT-4o
AGENT_B_PROVIDER = OpenAIProvider()       # Vulnerability Analyst → GPT-4o
AGENT_C_PROVIDER = OpenAIProvider()       # Impact Assessor       → GPT-4o
JUDGE_PROVIDER   = ClaudeProvider()       # Judge                 → Claude Sonnet
```

#### Swap example — mixed models per agent:

```python
AGENT_A_PROVIDER = ClaudeProvider("claude-opus-4-5")   # Best reasoning for classification
AGENT_B_PROVIDER = OpenAIProvider("gpt-4o")            # GPT-4o for CVE mapping
AGENT_C_PROVIDER = OpenAIProvider("gpt-4-turbo")       # GPT Turbo for impact scoring
JUDGE_PROVIDER   = ClaudeProvider()                    # Claude Sonnet as judge
```

---

## Agent Prompts (Full Text)

Prompts live in `prompts/` as plain `.txt` files. Each agent loads its own at startup via `load_prompt()`. Keeping them as files means you can version-control prompt changes separately from code changes — useful when iterating for your IEEE paper.

---

### `prompts/prompt_a.txt` — Agent A: Threat Classifier

```
You are a cybersecurity threat classification specialist with 10 years of experience.
When given a description of a cyber threat or attack, your job is ONLY to classify the threat type.

You must output exactly three things:

1. THREAT CATEGORY — choose one only:
   Phishing | Malware | SQL Injection | DDoS | Ransomware |
   Zero-Day Exploit | Insider Threat | Man-in-the-Middle | Other

2. CONFIDENCE SCORE — a percentage from 0% to 100%

3. JUSTIFICATION — one sentence explaining your classification.
   Reference specific indicators from the threat description.

Rules:
- Do NOT provide remediation advice
- Do NOT discuss CVEs or vulnerabilities
- Do NOT assess severity or impact
- Focus ONLY on identifying and justifying the threat category
```

**Why this prompt is written this way:** Strict output format (category + score + justification) gives the judge structured, comparable data. Banning advice and CVE discussion keeps each agent in its lane — this specialization is what makes the council design work.

---

### `prompts/prompt_b.txt` — Agent B: Vulnerability Analyst

```
You are a CVE (Common Vulnerabilities and Exposures) analyst and MITRE ATT&CK framework expert.
When given a cyber threat description, your job is to map the attack to known frameworks.

You must output exactly:

1. CVE STATUS — either a specific CVE ID (e.g., CVE-2021-44228) or "No known CVE"

2. MITRE ATT&CK TACTIC — the high-level goal of the attacker, e.g.:
   Initial Access | Execution | Persistence | Privilege Escalation |
   Defense Evasion | Credential Access | Discovery | Lateral Movement |
   Collection | Exfiltration | Impact

3. MITRE ATT&CK TECHNIQUE ID — the specific technique code, e.g.:
   T1566 (Phishing) | T1190 (Exploit Public-Facing Application) | T1059 (Command and Scripting)

4. ATTACK CHAIN — a brief 2 to 3 step description of how the attack progresses

5. AFFECTED SYSTEMS — which software, OS, or services are targeted

Rules:
- Do NOT classify the threat type
- Do NOT suggest defensive actions
- Do NOT score severity
- Focus ONLY on CVE mapping, MITRE framework, and affected systems
```

**Why this prompt is written this way:** Requiring the MITRE technique ID (e.g., T1566) gives the judge structured, standardized data — not just free-form text. MITRE ATT&CK is the industry standard framework used in real SOC operations, which strengthens your IEEE paper's credibility.

---

### `prompts/prompt_c.txt` — Agent C: Impact Assessor

```
You are a cybersecurity risk manager and business impact analyst.
When given a cyber threat description, your job is to assess the real-world damage potential.

You must output exactly:

1. SEVERITY SCORE — a number from 1 to 10 using these anchors:
   1 to 3  : Low    — minor inconvenience, easily reversible
   4 to 6  : Medium — significant disruption, some data at risk
   7 to 9  : High   — major breach, financial loss, regulatory impact
   10      : Critical — national infrastructure or mass casualty potential

2. AFFECTED SCOPE — choose one:
   Individual | Small Team | Organization | Sector-Wide | National Infrastructure

3. POTENTIAL IMPACT — list ALL that apply:
   Data Loss | Financial Loss | Service Disruption | Reputational Damage |
   Regulatory Penalty | Physical Harm | National Security Risk

4. TOP 3 IMMEDIATE ACTIONS — numbered, in priority order.
   Write as direct instructions to the victim (e.g., "Block the sender domain immediately").

Rules:
- Do NOT classify the threat type
- Do NOT reference CVEs or ATT&CK techniques
- Do NOT repeat the threat description back
- Focus ONLY on damage potential and defensive response
```

**Why this prompt is written this way:** The severity scale with explicit anchors forces consistent scoring across different threats and different agents. This consistency is what makes your evaluation metrics statistically meaningful across dataset runs.

---

### `prompts/prompt_judge.txt` — Judge Agent

```
You are a Chief Information Security Officer (CISO) acting as the final decision authority.
You will receive a cyber threat description followed by three independent specialist analyses:
  - Agent A: Threat Classifier
  - Agent B: Vulnerability Analyst
  - Agent C: Impact Assessor

Your job is to synthesize all three reports into ONE authoritative final threat assessment.

You must output:

1. FINAL CLASSIFICATION — confirm or correct Agent A's category with one sentence of reasoning

2. FINAL CVE AND MITRE MAPPING — confirm or correct Agent B's mapping.
   If agents conflict, state which you trust and why.

3. FINAL SEVERITY — confirm or adjust Agent C's score (1–10) with a one-sentence rationale

4. CONTRADICTION REPORT — list any contradictions between agents, or write "No contradictions".
   For each contradiction found, state your resolution and reasoning.

5. FINAL RESPONSE PLAN — numbered actions in priority order.
   Build on Agent C's actions but expand or reorder based on the full picture from all agents.

Rules:
- You are the final authority. Do not hedge with phrases like "it could be" or "possibly"
- If two agents agree and one disagrees, explain whether the dissenter raises a valid point
- Your output must be usable by a real security team within 5 minutes of reading it
- Be decisive. Be precise. No filler sentences.
```

**Why this prompt is written this way:** The "no hedging" and "usable in 5 minutes" rules force the judge to produce a clean, actionable report rather than a vague summary. The contradiction report is the most novel part of this architecture — it is what differentiates the council from a simple ensemble and is the strongest claim in your IEEE paper.

---

## Agent Implementation

### `agents/base_agent.py`

```python
from abc import ABC, abstractmethod
from providers.base_provider import BaseLLMProvider

class BaseAgent(ABC):
    """
    Abstract base for all council agents.
    Agents never import a specific LLM library — they only use BaseLLMProvider.
    This is what makes the provider swap fully transparent to the agent layer.
    """

    def __init__(self, name: str, system_prompt: str, provider: BaseLLMProvider):
        self.name          = name
        self.system_prompt = system_prompt
        self.provider      = provider

    def analyze(self, threat: str) -> dict:
        output = self.provider.complete(
            system_prompt=self.system_prompt,
            user_message=threat
        )
        return {
            "agent":    self.name,
            "provider": self.provider.provider_name(),
            "output":   output
        }

    @staticmethod
    def load_prompt(path: str) -> str:
        with open(path, "r") as f:
            return f.read().strip()
```

---

### `agents/classifier_agent.py`

```python
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_A_PROVIDER

class ClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Threat Classifier",
            system_prompt=self.load_prompt("prompts/prompt_a.txt"),
            provider=AGENT_A_PROVIDER          # pulled from config — never hardcoded
        )
```

Create `vuln_agent.py` and `impact_agent.py` identically — only the name, prompt path, and provider constant differ:

```python
# agents/vuln_agent.py
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_B_PROVIDER

class VulnAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Vulnerability Analyst",
            system_prompt=self.load_prompt("prompts/prompt_b.txt"),
            provider=AGENT_B_PROVIDER
        )
```

```python
# agents/impact_agent.py
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_C_PROVIDER

class ImpactAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Impact Assessor",
            system_prompt=self.load_prompt("prompts/prompt_c.txt"),
            provider=AGENT_C_PROVIDER
        )
```

---

### `agents/judge_agent.py`

```python
from agents.base_agent import BaseAgent
from config.agent_config import JUDGE_PROVIDER

class JudgeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Judge (CISO)",
            system_prompt=self.load_prompt("prompts/prompt_judge.txt"),
            provider=JUDGE_PROVIDER             # pulled from config
        )

    def synthesize(self, threat: str, agent_outputs: list) -> dict:
        """
        Build a combined input from all agent outputs and run the judge.
        The judge sees which provider each agent used — useful for mixed-model runs.
        """
        combined = "\n\n".join(
            f"=== {r['agent']} (via {r['provider']}) ===\n{r['output']}"
            for r in agent_outputs
        )
        judge_input = f"Original Threat:\n{threat}\n\n{combined}"
        return self.analyze(judge_input)
```

---

### `council/orchestrator.py`

```python
from agents.classifier_agent import ClassifierAgent
from agents.vuln_agent import VulnAgent
from agents.impact_agent import ImpactAgent
from agents.judge_agent import JudgeAgent

class CyberCouncil:
    def __init__(self):
        self.agents = [
            ClassifierAgent(),
            VulnAgent(),
            ImpactAgent(),
        ]
        self.judge = JudgeAgent()

    def analyze(self, threat: str) -> dict:
        # Step 1 — All 3 agents analyze independently
        agent_outputs = [agent.analyze(threat) for agent in self.agents]

        # Step 2 — Judge synthesizes all outputs into one report
        final = self.judge.synthesize(threat, agent_outputs)

        return {
            "threat":        threat,
            "agent_outputs": agent_outputs,
            "final_report":  final["output"]
        }
```

---

## Running the Project

### Single threat test

```python
# main.py
from council.orchestrator import CyberCouncil

threat = """
An employee received an email from ceo-financials.com claiming to be the CEO,
requesting an urgent wire transfer of $150,000 to an external account.
The link in the email points to http://docusign-secure.ceo-financials.com/sign.
Email was sent at 2:47 AM. The real company domain is company.com.
"""

council = CyberCouncil()
result  = council.analyze(threat)

for output in result["agent_outputs"]:
    print(f"\n{'='*60}")
    print(f"[{output['agent']}]  via {output['provider']}")
    print(output["output"])

print(f"\n{'='*60}")
print("[FINAL JUDGE REPORT]")
print(result["final_report"])
```

```bash
python main.py
```

---

## Dataset Format

`data/sample_threats.json`:

```json
[
  {
    "id": 1,
    "threat_description": "Email from spoofed CEO domain requesting urgent wire transfer with fake DocuSign link.",
    "true_label": "Phishing"
  },
  {
    "id": 2,
    "threat_description": "Login form receives payload: admin' OR '1'='1'; DROP TABLE users; --",
    "true_label": "SQL Injection"
  },
  {
    "id": 3,
    "threat_description": "Server receives 847 requests/sec from 1200 different IPs. Legitimate traffic blocked.",
    "true_label": "DDoS"
  },
  {
    "id": 4,
    "threat_description": "All files on the network share are encrypted. A ransom note demands $500,000 in Bitcoin.",
    "true_label": "Ransomware"
  },
  {
    "id": 5,
    "threat_description": "Antivirus detects outbound traffic to 185.220.101.x. System processes silently spawning cmd.exe.",
    "true_label": "Malware"
  }
]
```

For your IEEE paper, replace these with real labeled samples from **UNSW-NB15**, **CIC-IDS-2017**, or **PhishTank**.

---

## Evaluation

### `evaluation/metrics.py`

```python
from sklearn.metrics import (
    accuracy_score, precision_score,
    recall_score, f1_score, classification_report
)

def compute_metrics(true_labels: list, predicted_labels: list) -> dict:
    return {
        "accuracy":  accuracy_score(true_labels, predicted_labels),
        "precision": precision_score(true_labels, predicted_labels, average="weighted", zero_division=0),
        "recall":    recall_score(true_labels, predicted_labels, average="weighted", zero_division=0),
        "f1_score":  f1_score(true_labels, predicted_labels, average="weighted", zero_division=0),
        "report":    classification_report(true_labels, predicted_labels, zero_division=0)
    }
```

### `evaluation/evaluator.py`

```python
import json
from tqdm import tqdm
from council.orchestrator import CyberCouncil
from evaluation.metrics import compute_metrics

LABEL_MAP = ["Phishing", "Malware", "SQL Injection", "DDoS", "Ransomware", "Other"]

def extract_label(text: str) -> str:
    for label in LABEL_MAP:
        if label.lower() in text.lower():
            return label
    return "Other"

def run_evaluation(dataset_path: str):
    with open(dataset_path) as f:
        dataset = json.load(f)

    council = CyberCouncil()
    true_labels, pred_labels = [], []

    for item in tqdm(dataset, desc="Evaluating"):
        result    = council.analyze(item["threat_description"])
        predicted = extract_label(result["final_report"])
        true_labels.append(item["true_label"])
        pred_labels.append(predicted)

    return compute_metrics(true_labels, pred_labels), true_labels, pred_labels
```

### `run_eval.py`

```python
from evaluation.evaluator import run_evaluation
import json

metrics, true_labels, pred_labels = run_evaluation("data/sample_threats.json")

print("\n===== EVALUATION RESULTS =====")
print(f"Accuracy  : {metrics['accuracy']:.4f}")
print(f"Precision : {metrics['precision']:.4f}")
print(f"Recall    : {metrics['recall']:.4f}")
print(f"F1 Score  : {metrics['f1_score']:.4f}")
print("\nClassification Report:")
print(metrics["report"])

with open("results/eval_results.json", "w") as f:
    json.dump({
        "accuracy":    metrics["accuracy"],
        "precision":   metrics["precision"],
        "recall":      metrics["recall"],
        "f1_score":    metrics["f1_score"],
        "predictions": list(zip(true_labels, pred_labels))
    }, f, indent=2)

print("\nSaved to results/eval_results.json")
```

```bash
python run_eval.py
```

---

## Adding a New Provider

To add Gemini, Mistral, or any future LLM — create one file and update config:

```python
# providers/gemini_provider.py
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

Then in `config/agent_config.py`:

```python
from providers.gemini_provider import GeminiProvider
AGENT_A_PROVIDER = GeminiProvider()    # done — zero other changes
```

---

## Baselines (Required for IEEE Paper)

### Baseline 1 — Single Agent (no council)

```python
output = AGENT_A_PROVIDER.complete(
    system_prompt="You are a cybersecurity expert. Classify this threat as one of: Phishing, Malware, SQL Injection, DDoS, Ransomware, Other. Output the label only.",
    user_message=threat
)
```

### Baseline 2 — Majority Vote (no judge)

```python
from collections import Counter
labels    = [extract_label(o["output"]) for o in agent_outputs]
predicted = Counter(labels).most_common(1)[0][0]
```

### Results Table

| System                          | Accuracy | Precision | Recall | F1 Score |
| ------------------------------- | -------- | --------- | ------ | -------- |
| Baseline 1 — Single Agent       | —        | —         | —      | —        |
| Baseline 2 — Majority Vote      | —        | —         | —      | —        |
| **Ours — Full Council + Judge** | —        | —         | —      | —        |

---

## Ablation Study

| Configuration               | Notes                  | F1 Score |
| --------------------------- | ---------------------- | -------- |
| Agent A + B + Judge (no C)  | Remove impact assessor | —        |
| Agent A + C + Judge (no B)  | Remove vuln analyst    | —        |
| Agent B + C + Judge (no A)  | Remove classifier      | —        |
| All 3 Agents, Majority Vote | Remove judge           | —        |
| **All 3 Agents + Judge**    | Full system            | —        |

---

## Environment Variables

| Variable            | Used By                     |
| ------------------- | --------------------------- |
| `ANTHROPIC_API_KEY` | `ClaudeProvider`            |
| `OPENAI_API_KEY`    | `OpenAIProvider`            |
| `GOOGLE_API_KEY`    | `GeminiProvider` (if added) |

---

## Design Principles

**Open/Closed Principle:** Agents are closed to modification but open to extension. Adding GPT-5 means one new file and one line in config — nothing else changes.

**Config-driven assembly:** All provider-to-agent wiring is in `config/agent_config.py`. This makes the system fast to experiment with and easy to document in your paper's implementation section.

**Prompts as files:** Prompts are `.txt` files, not hardcoded strings. You can iterate on prompts without touching Python code, and commit prompt versions separately in git.

**Provider name in output:** Every agent result includes the `provider_name()` string. The judge sees which model produced each analysis — useful for cross-model ablation studies in the paper.

---

## Paper Contribution Summary

1. **Novel architecture** — domain-specific multi-agent council with judge synthesizer for cybersecurity threat analysis
2. **Extensible provider design** — any agent can use any LLM; enables cross-model ablation studies
3. **Quantitative improvement** — F1 improvement over single-agent baseline on public benchmark
4. **Ablation study** — proves each component independently contributes to accuracy

---

## License

MIT — free to use and modify for research purposes.
