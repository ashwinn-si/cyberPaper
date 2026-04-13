# CyberCouncil — New Agents Implementation Guide

> Covers: Validator Agent (Agent 0), Remediation Agent (Agent D), parallel agent execution,
> two-round evaluation, and local testing setup.
> Everything is additive — no existing file is deleted.

---

## What This Guide Adds

| #   | What                                                  | Where                                                        |
| --- | ----------------------------------------------------- | ------------------------------------------------------------ |
| 1   | `Agent 0` — Validator / Preprocessor                  | `agents/validator_agent.py` + `prompts/prompt_validator.txt` |
| 2   | `Agent D` — Remediation Agent                         | `agents/remediation_agent.py` + `prompts/prompt_d.txt`       |
| 3   | Parallel execution with `asyncio`                     | `council/orchestrator.py` — full replacement                 |
| 4   | Two-round evaluation loop                             | `council/orchestrator.py` — built into the same replacement  |
| 5   | `config/agent_config.py` — two new provider constants | `config/agent_config.py` — two lines appended                |
| 6   | Local test runner                                     | `tests/test_local.py` — new file                             |

---

## Execution Order

```
Step 1 → Create prompts/prompt_validator.txt
Step 2 → Create prompts/prompt_d.txt
Step 3 → Create agents/validator_agent.py
Step 4 → Create agents/remediation_agent.py
Step 5 → Edit config/agent_config.py  (append 2 lines)
Step 6 → Replace council/orchestrator.py
Step 7 → Create tests/test_local.py
Step 8 → Run local test
```

---

## Step 1 — Create `prompts/prompt_validator.txt`

Create this file at `prompts/prompt_validator.txt` with the following content exactly:

```
You are a cybersecurity input validation and enrichment specialist.
Your only job is to check whether a user-submitted threat description is usable
for analysis, and either pass it, enrich it, or ask one round of clarifying questions.

You will operate in one of two modes depending on what you receive:

────────────────────────────────────────────
MODE A — FIRST PASS (raw user input only)
────────────────────────────────────────────

Evaluate the input against these three criteria:

1. RELEVANCE — Is this related to a cybersecurity threat or incident?
   Reject: "hello", "stupid", "test", random words, non-security topics.

2. SPECIFICITY — Does it contain enough detail to analyze?
   Vague examples: "my computer is hacked", "something weird happened", "network issue".
   These need clarification.

3. CLARITY — Is it coherent enough to understand?
   Poorly written but understandable inputs can be enriched without questions.

Based on your evaluation, output EXACTLY one of these three responses:

RESPONSE TYPE 1 — INVALID (not a security threat at all):
  STATUS: Invalid
  REASON: <one sentence explaining why this is not a valid threat description>
  ACTION: Ask the user to describe a specific cybersecurity threat or incident.

RESPONSE TYPE 2 — NEEDS CLARIFICATION (security-related but too vague):
  STATUS: Needs Clarification
  QUESTIONS:
  1. <targeted question 1 — ask about what specifically happened>
  2. <targeted question 2 — ask about timing, scope, or systems affected>
  3. <targeted question 3 — ask about any visible indicators or symptoms> (optional, only if needed)

  Rules for questions:
  - Maximum 3 questions. Ask only what you genuinely need.
  - Each question must be specific, not generic ("What systems are affected?" not "Tell me more")
  - Do NOT ask questions if the input already contains enough for analysis

RESPONSE TYPE 3 — PASS (sufficient detail):
  STATUS: Pass
  ENRICHED THREAT: <rewrite the input as a clean, professional 2-4 sentence threat description.
                    Fix grammar, add implied context, use standard cybersecurity terminology.
                    Do not invent facts — only clarify what is already stated.>

────────────────────────────────────────────────────────
MODE B — SECOND PASS (original input + user's answers)
────────────────────────────────────────────────────────

You will receive the original input AND the user's answers to your questions.
In this mode you MUST always output STATUS: Pass — no more questions, no rejection.
Merge the original input and the answers into one clean threat description.

  STATUS: Pass
  ENRICHED THREAT: <merged, professional 2-4 sentence threat description>

Rules for Mode B:
- Always produce a Pass even if the answers are vague or unhelpful
- Use whatever context the user provided — do your best
- Never ask a third round of questions under any circumstances

────────────────────────────────
GLOBAL RULES (both modes)
────────────────────────────────
- Do NOT perform threat classification
- Do NOT suggest remediation steps
- Do NOT reference CVE IDs or MITRE ATT&CK
- Your only output is the structured response shown above — no extra commentary
```

---

## Step 2 — Create `prompts/prompt_d.txt`

Create this file at `prompts/prompt_d.txt` with the following content exactly:

```
You are a senior cybersecurity remediation engineer with expertise in incident response,
patch management, and security hardening.

When given a cybersecurity threat description, your job is to prescribe the exact technical fix.

You must output exactly:

1. PATCH / FIX
   The specific technical remediation — software patch, configuration change, firewall rule,
   or policy update needed. If a CVE patch exists, name it. If not, describe the config fix.

2. CONTAINMENT (immediate — within the next 30 minutes)
   Numbered steps to stop the active threat right now.
   Write as direct commands to the incident responder.
   Maximum 4 steps. Be specific — "Block outbound traffic on port 445" not "check network."

3. TOOLS TO DEPLOY
   List specific security tools needed for detection, containment, or forensics.
   Name the actual tool (e.g., CrowdStrike, Wireshark, Sysmon, Splunk SIEM rule).
   If no specific tool applies, write "Standard EDR and SIEM alerting sufficient."

4. LONG-TERM HARDENING (implement within 72 hours)
   Numbered steps to prevent recurrence.
   Cover: configuration, policy, monitoring, and user awareness as applicable.
   Maximum 5 steps.

5. RECOVERY STEPS
   How to restore normal operations after containment.
   Cover: data restoration, system verification, stakeholder notification, evidence preservation.

Rules:
- Do NOT classify the threat type — that is Agent A's job
- Do NOT reference MITRE ATT&CK technique IDs — that is Agent B's job
- Do NOT score severity — that is Agent C's job
- Your entire focus is: how do we fix this and prevent it from happening again
- Be specific enough that a junior security analyst can execute your steps without Googling
- If the threat is ambiguous, prescribe for the most dangerous plausible interpretation
```

---

## Step 3 — Create `agents/validator_agent.py`

Create this file at `agents/validator_agent.py`:

```python
import re
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_VALIDATOR_PROVIDER


class ValidatorAgent(BaseAgent):
    """
    Agent 0 — Threat Validator and Preprocessor.

    Operates in two passes:
      Pass 1 (first_pass=True)  : evaluates raw input, may ask questions or pass directly
      Pass 2 (first_pass=False) : merges original input + user answers, always passes

    The council calls pass_one() first. If questions are returned, the council
    collects user answers and calls pass_two(). After pass_two(), the enriched
    threat goes to Agents A, B, C, D. No third pass ever occurs.
    """

    def __init__(self):
        super().__init__(
            name="Validator",
            system_prompt=self.load_prompt("prompts/prompt_validator.txt"),
            provider=AGENT_VALIDATOR_PROVIDER
        )

    def pass_one(self, raw_input: str) -> dict:
        """
        First pass: evaluate raw user input.

        Returns dict with keys:
          status  : "Invalid" | "Needs Clarification" | "Pass"
          output  : full raw LLM output
          questions : list[str] if status == "Needs Clarification", else []
          enriched  : str if status == "Pass", else ""
        """
        result = self.analyze(raw_input)
        return self._parse_output(result["output"])

    def pass_two(self, raw_input: str, user_answers: str) -> dict:
        """
        Second pass: merge original input + user answers into enriched threat.
        Always returns status == "Pass".

        Args:
            raw_input    : the original user-submitted threat description
            user_answers : the user's answers to the clarifying questions
        """
        combined = (
            f"ORIGINAL INPUT:\n{raw_input}\n\n"
            f"USER'S ANSWERS TO CLARIFYING QUESTIONS:\n{user_answers}\n\n"
            f"This is the second pass. You must output STATUS: Pass and an ENRICHED THREAT."
        )
        result = self.analyze(combined)
        parsed = self._parse_output(result["output"])
        # Hard enforce Pass on second pass regardless of model output
        parsed["status"] = "Pass"
        return parsed

    def _parse_output(self, text: str) -> dict:
        """Parse structured LLM output into a clean dict."""
        status_match = re.search(r"STATUS:\s*(Invalid|Needs Clarification|Pass)", text, re.IGNORECASE)
        status = status_match.group(1).strip() if status_match else "Pass"

        questions = []
        if status == "Needs Clarification":
            q_matches = re.findall(r"^\s*\d+\.\s+(.+)$", text, re.MULTILINE)
            questions = [q.strip() for q in q_matches if q.strip()]

        enriched = ""
        enriched_match = re.search(r"ENRICHED THREAT:\s*(.+?)(?:\n\n|\Z)", text, re.DOTALL)
        if enriched_match:
            enriched = enriched_match.group(1).strip()

        reason = ""
        reason_match = re.search(r"REASON:\s*(.+?)(?:\n|$)", text)
        if reason_match:
            reason = reason_match.group(1).strip()

        return {
            "status":    status,
            "output":    text,
            "questions": questions,
            "enriched":  enriched,
            "reason":    reason,
        }
```

---

## Step 4 — Create `agents/remediation_agent.py`

Create this file at `agents/remediation_agent.py`:

```python
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_D_PROVIDER


class RemediationAgent(BaseAgent):
    """
    Agent D — Remediation Engineer.
    Prescribes the exact technical fix: patches, containment steps,
    tools, long-term hardening, and recovery steps.
    """

    def __init__(self):
        super().__init__(
            name="Remediation Engineer",
            system_prompt=self.load_prompt("prompts/prompt_d.txt"),
            provider=AGENT_D_PROVIDER
        )
```

---

## Step 5 — Edit `config/agent_config.py`

Append these two lines to the existing constants block. Do not remove or replace anything.

```python
AGENT_VALIDATOR_PROVIDER = ClaudeProvider()   # Agent 0 — Validator
AGENT_D_PROVIDER         = ClaudeProvider()   # Agent D — Remediation Engineer
```

The full file after the edit should look like:

```python
from providers.claude_provider import ClaudeProvider
from providers.openai_provider import OpenAIProvider

AGENT_A_PROVIDER         = ClaudeProvider()   # Threat Classifier
AGENT_B_PROVIDER         = ClaudeProvider()   # Vulnerability Analyst
AGENT_C_PROVIDER         = ClaudeProvider()   # Impact Assessor
JUDGE_PROVIDER           = ClaudeProvider()   # Judge / Synthesizer
AGENT_VALIDATOR_PROVIDER = ClaudeProvider()   # Agent 0 — Validator
AGENT_D_PROVIDER         = ClaudeProvider()   # Agent D — Remediation Engineer
```

---

## Step 6 — Replace `council/orchestrator.py`

Replace the entire file with the following. This adds:

- `ValidatorAgent` and `RemediationAgent` wired in
- All 4 specialist agents (A, B, C, D) running in **parallel** via `asyncio`
- Two-round evaluation with the Judge
- `analyze_sync()` as a convenience wrapper for non-async callers

```python
"""
CyberCouncil Orchestrator
─────────────────────────
Flow:
  1. ValidatorAgent (Agent 0) — validates and enriches raw input (1–2 passes)
  2. Agents A, B, C, D       — run IN PARALLEL on the enriched threat (Round 1)
  3. JudgeAgent              — synthesizes Round 1 outputs → draft report
  4. Agents A, B, C, D       — run IN PARALLEL with draft report as context (Round 2)
  5. JudgeAgent              — synthesizes Round 2 outputs → final report

Parallel execution uses asyncio + ThreadPoolExecutor so each agent's blocking
API call runs in its own thread. On a 4-agent council this cuts wall-clock time
by ~3–4x compared to sequential execution.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from agents.classifier_agent  import ClassifierAgent
from agents.vuln_agent         import VulnAgent
from agents.impact_agent       import ImpactAgent
from agents.judge_agent        import JudgeAgent
from agents.validator_agent    import ValidatorAgent
from agents.remediation_agent  import RemediationAgent


# Shared thread pool — one pool per process, reused across analyze() calls
_EXECUTOR = ThreadPoolExecutor(max_workers=8)


class CyberCouncil:

    def __init__(self):
        self.validator  = ValidatorAgent()
        self.agents     = [
            ClassifierAgent(),    # Agent A
            VulnAgent(),          # Agent B
            ImpactAgent(),        # Agent C
            RemediationAgent(),   # Agent D
        ]
        self.judge = JudgeAgent()

    # ── Public entry points ────────────────────────────────────────────────

    def analyze_sync(self, threat: str, user_answers: str = "") -> dict:
        """
        Synchronous wrapper around analyze().
        Safe to call from non-async code (main.py, run_eval.py, Flask routes).

        Args:
            threat       : raw user input
            user_answers : answers to validator's clarifying questions (if any).
                           Pass empty string "" if not applicable.
        """
        return asyncio.run(self.analyze(threat, user_answers))

    async def analyze(self, threat: str, user_answers: str = "") -> dict:
        """
        Full async pipeline.

        Returns dict with keys:
          status           : "rejected" | "analyzed"
          original_input   : raw user input
          clean_threat     : enriched threat used for analysis (empty if rejected)
          validation       : full validator output dict
          round1_outputs   : list of agent dicts from Round 1
          draft_report     : Judge's Round 1 synthesis
          round2_outputs   : list of agent dicts from Round 2
          final_report     : Judge's final synthesis
        """
        loop = asyncio.get_event_loop()

        # ── Step 0: Validation ─────────────────────────────────────────────
        validation = await loop.run_in_executor(
            _EXECUTOR, self.validator.pass_one, threat
        )

        if validation["status"] == "Invalid":
            return {
                "status":         "rejected",
                "original_input": threat,
                "clean_threat":   "",
                "validation":     validation,
                "round1_outputs": [],
                "draft_report":   "",
                "round2_outputs": [],
                "final_report":   "",
            }

        if validation["status"] == "Needs Clarification":
            # If caller passed answers already (e.g. from server.py collecting them),
            # run pass_two immediately. Otherwise surface questions to the caller.
            if user_answers.strip():
                validation = await loop.run_in_executor(
                    _EXECUTOR,
                    lambda: self.validator.pass_two(threat, user_answers)
                )
            else:
                return {
                    "status":         "needs_clarification",
                    "original_input": threat,
                    "clean_threat":   "",
                    "validation":     validation,
                    "questions":      validation["questions"],
                    "round1_outputs": [],
                    "draft_report":   "",
                    "round2_outputs": [],
                    "final_report":   "",
                }

        clean_threat = validation.get("enriched") or threat

        # ── Step 1: Round 1 — all agents in parallel ───────────────────────
        round1_outputs = await self._run_agents_parallel(clean_threat, loop)

        # ── Step 2: Judge synthesizes Round 1 ─────────────────────────────
        draft_report = await loop.run_in_executor(
            _EXECUTOR,
            lambda: self.judge.synthesize(clean_threat, round1_outputs)
        )

        # ── Step 3: Round 2 — agents re-analyze with draft context ────────
        round2_input = (
            f"{clean_threat}\n\n"
            f"--- JUDGE DRAFT REPORT (Round 1) ---\n{draft_report['output']}"
        )
        round2_outputs = await self._run_agents_parallel(round2_input, loop)

        # ── Step 4: Judge synthesizes Round 2 → final report ──────────────
        final_report = await loop.run_in_executor(
            _EXECUTOR,
            lambda: self.judge.synthesize(clean_threat, round2_outputs)
        )

        return {
            "status":          "analyzed",
            "original_input":  threat,
            "clean_threat":    clean_threat,
            "validation":      validation,
            "round1_outputs":  round1_outputs,
            "draft_report":    draft_report["output"],
            "round2_outputs":  round2_outputs,
            "final_report":    final_report["output"],
        }

    # ── Internal helpers ───────────────────────────────────────────────────

    async def _run_agents_parallel(self, threat_input: str, loop) -> list:
        """
        Run all 4 specialist agents concurrently.
        Each agent's blocking .analyze() call runs in its own thread.
        Returns list of agent output dicts in agent order (A, B, C, D).
        """
        tasks = [
            loop.run_in_executor(_EXECUTOR, agent.analyze, threat_input)
            for agent in self.agents
        ]
        return list(await asyncio.gather(*tasks))
```

---

## Step 7 — Create `tests/test_local.py`

Create this file at `tests/test_local.py`. Run it with `python tests/test_local.py` to verify
everything works end-to-end before running the full evaluation.

```python
"""
Local test runner for CyberCouncil.
Tests all paths: valid threat, vague threat with answers, and invalid input.
Run with: python tests/test_local.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from council.orchestrator import CyberCouncil


# ── Test cases ─────────────────────────────────────────────────────────────

TESTS = [
    {
        "name":         "1 — Clear threat (should go straight through)",
        "threat":       "All files on the network share are encrypted. A ransom note demands $500,000 in Bitcoin within 48 hours.",
        "user_answers": "",
    },
    {
        "name":         "2 — Vague threat with answers supplied",
        "threat":       "my computer is acting weird",
        "user_answers": "It started after I opened an email attachment. Lots of pop-ups and the fan is running loud. Just my laptop, Windows 11.",
    },
    {
        "name":         "3 — Invalid input (should be rejected)",
        "threat":       "stupid",
        "user_answers": "",
    },
    {
        "name":         "4 — Phishing (parallel agents stress test)",
        "threat":       "An employee received an email from ceo-financials.com claiming to be the CEO, requesting an urgent wire transfer of $150,000. The link points to http://docusign-secure.ceo-financials.com/sign. Sent at 2:47 AM.",
        "user_answers": "",
    },
]


# ── Runner ─────────────────────────────────────────────────────────────────

def print_separator(label=""):
    print("\n" + "=" * 65)
    if label:
        print(f"  {label}")
        print("=" * 65)


def run_test(council: CyberCouncil, test: dict):
    print_separator(test["name"])
    print(f"INPUT : {test['threat']}")
    if test["user_answers"]:
        print(f"ANSWERS: {test['user_answers']}")

    result = council.analyze_sync(test["threat"], test["user_answers"])

    status = result["status"]
    print(f"\nSTATUS: {status.upper()}")

    if status == "rejected":
        print(f"REASON: {result['validation'].get('reason', 'N/A')}")
        return

    if status == "needs_clarification":
        print("QUESTIONS:")
        for i, q in enumerate(result.get("questions", []), 1):
            print(f"  {i}. {q}")
        return

    # Analyzed — print summary
    print(f"\nCLEAN THREAT:\n{result['clean_threat']}\n")

    print("── ROUND 1 AGENT OUTPUTS ──")
    for out in result["round1_outputs"]:
        print(f"\n[{out['agent']}] via {out['provider']}")
        # Print first 300 chars to keep terminal readable
        preview = out["output"][:300].replace("\n", " ")
        print(f"  {preview}{'...' if len(out['output']) > 300 else ''}")

    print(f"\n── DRAFT REPORT (Round 1 Judge) ──")
    draft_preview = result["draft_report"][:400].replace("\n", " ")
    print(f"  {draft_preview}{'...' if len(result['draft_report']) > 400 else ''}")

    print(f"\n── FINAL REPORT (Round 2 Judge) ──")
    print(result["final_report"])


def main():
    print("\nCyberCouncil — Local Test Runner")
    print("Initializing council...")

    council = CyberCouncil()

    for test in TESTS:
        try:
            run_test(council, test)
        except Exception as e:
            print(f"\n[ERROR in test '{test['name']}']: {e}")
            import traceback
            traceback.print_exc()

    print_separator("All tests complete")


if __name__ == "__main__":
    main()
```

---

## Step 8 — Run Local Test

```bash
# From the project root
python tests/test_local.py
```

Expected output for each test case:

| Test                 | Expected Status | What to verify                                    |
| -------------------- | --------------- | ------------------------------------------------- |
| 1 — Clear ransomware | `ANALYZED`      | All 4 agents output, draft + final report present |
| 2 — Vague + answers  | `ANALYZED`      | Enriched threat merges original + answers         |
| 3 — "stupid"         | `REJECTED`      | Reason printed, no agent calls made               |
| 4 — Phishing         | `ANALYZED`      | Parallel execution — all 4 agents complete        |

---

## Updated Agent Table (Full System)

| Agent                         | File                   | Role                       | Output                                                |
| ----------------------------- | ---------------------- | -------------------------- | ----------------------------------------------------- |
| **0 — Validator**             | `validator_agent.py`   | Gatekeeps + enriches input | Status · Questions (if needed) · Enriched threat      |
| **A — Classifier**            | `classifier_agent.py`  | Identifies attack type     | Category + confidence %                               |
| **B — Vulnerability Analyst** | `vuln_agent.py`        | Maps CVE + MITRE           | CVE ID · ATT&CK tactic + technique                    |
| **C — Impact Assessor**       | `impact_agent.py`      | Scores damage potential    | Severity 1–10 · impact types                          |
| **D — Remediation**           | `remediation_agent.py` | Prescribes the fix         | Patch · containment · tools · hardening · recovery    |
| **Judge (CISO)**              | `judge_agent.py`       | Synthesizes all 4 reports  | Final report · contradiction resolution · action plan |

---

## Updated Full Pipeline

```
User Input (raw, possibly vague or garbage)
        │
        ▼
┌─────────────────────────────┐
│  Agent 0 — Validator        │──── Invalid ────► Reject + explain
│  Pass 1: evaluate           │
│  Pass 2: merge answers      │──── Needs Clarification ──► Ask questions ──► Pass 2
└────────────┬────────────────┘
             │ Enriched threat
             ▼
┌────────────────────────────────────────────────────────────┐
│                    ROUND 1 (parallel)                      │
│   Agent A ──┐                                              │
│   Agent B ──┼──► asyncio.gather() ──► 4 outputs at once   │
│   Agent C ──┤                                              │
│   Agent D ──┘                                              │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
                     Judge → Draft Report
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│           ROUND 2 (parallel) — agents see draft            │
│   Agent A ──┐                                              │
│   Agent B ──┼──► asyncio.gather() ──► 4 outputs at once   │
│   Agent C ──┤                                              │
│   Agent D ──┘                                              │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
                     Judge → Final Report
```

---

## Notes on Parallel Execution

- `asyncio.gather()` fires all 4 agent API calls simultaneously in separate threads
- Wall-clock time drops from ~`4 × latency` to ~`1 × latency` per round
- With 2 rounds + judge: total time ≈ `2 × agent_latency + 2 × judge_latency`
- `analyze_sync()` is the entry point for `main.py`, `run_eval.py`, and Flask routes — no async changes needed in those files
- If any single agent call fails, `asyncio.gather()` propagates the exception — wrap in try/except in `run_eval.py` if needed for robustness

---

## Definition of Done

- [ ] `prompts/prompt_validator.txt` exists with MODE A / MODE B structure
- [ ] `prompts/prompt_d.txt` exists with 5-section remediation output
- [ ] `agents/validator_agent.py` exists with `pass_one()`, `pass_two()`, `_parse_output()`
- [ ] `agents/remediation_agent.py` exists
- [ ] `config/agent_config.py` contains `AGENT_VALIDATOR_PROVIDER` and `AGENT_D_PROVIDER`
- [ ] `council/orchestrator.py` uses `asyncio` parallel execution and two-round Judge loop
- [ ] `tests/test_local.py` exists and runs without import errors
- [ ] `python tests/test_local.py` completes all 4 test cases with no exceptions
- [ ] `python main.py` still works (uses `analyze_sync()` — no changes needed to `main.py`)
- [ ] `python run_eval.py` still works (uses `analyze_sync()` — no changes needed)
