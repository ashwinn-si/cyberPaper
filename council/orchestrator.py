"""
CyberCouncil Orchestrator
─────────────────────────
Flow:
  1. ValidatorAgent (Agent 0) — validates and enriches raw input (1–2 passes)
  2. Agents A, A₂, B, C, C₂, D — run IN PARALLEL on the enriched threat
  3. Disagreement detection — A vs A₂ (classification), C vs C₂ (severity)
  4. JudgeAgent              — synthesizes outputs + disagreement log → final report

Parallel execution uses asyncio + ThreadPoolExecutor. All agents run concurrently.
Each agent's blocking API call runs in its own thread.
Wall-clock time: ~5–10 sec per threat.

For lower GPU memory (16GB), switch _run_agents_parallel to _run_agents_sequential.
"""

import asyncio
import concurrent.futures
import re
from concurrent.futures import ThreadPoolExecutor

from agents.classifier_agent   import ClassifierAgent
from agents.classifier_agent_2 import ClassifierAgent2
from agents.vuln_agent          import VulnAgent
from agents.impact_agent        import ImpactAgent
from agents.impact_agent_2      import ImpactAgent2
from agents.judge_agent         import JudgeAgent
from agents.validator_agent     import ValidatorAgent
from agents.remediation_agent   import RemediationAgent


# Shared thread pool — one pool per process, reused across analyze() calls
_EXECUTOR = ThreadPoolExecutor(max_workers=10)

# ── Lightweight output parsers for disagreement detection ─────────────────────

_CATEGORY_RE = re.compile(
    r"THREAT\s+CATEGORY\s*[:\-]\s*(.+)", re.IGNORECASE
)
_SEVERITY_RE = re.compile(
    r"SEVERITY\s+SCORE\s*[:\-]\s*(\d+)", re.IGNORECASE
)


def _extract_category(text: str) -> str | None:
    m = _CATEGORY_RE.search(text)
    return m.group(1).strip().lower() if m else None


def _extract_severity(text: str) -> int | None:
    m = _SEVERITY_RE.search(text)
    return int(m.group(1)) if m else None


def _agents_disagree_category(out_a: dict, out_a2: dict) -> bool:
    """True if A and A₂ produce different threat categories."""
    cat_a  = _extract_category(out_a["output"])
    cat_a2 = _extract_category(out_a2["output"])
    if cat_a is None or cat_a2 is None:
        return False
    return cat_a != cat_a2


def _agents_disagree_severity(out_c: dict, out_c2: dict, threshold: int = 2) -> bool:
    """True if C and C₂ severity scores differ by more than threshold."""
    sev_c  = _extract_severity(out_c["output"])
    sev_c2 = _extract_severity(out_c2["output"])
    if sev_c is None or sev_c2 is None:
        return False
    return abs(sev_c - sev_c2) > threshold



class CyberCouncil:

    def __init__(self):
        self.validator = ValidatorAgent()

        # Primary agents — indexed so we can pair A↔A₂ and C↔C₂ later
        self.agent_a  = ClassifierAgent()    # index 0
        self.agent_a2 = ClassifierAgent2()   # index 1  ← consensus pair for A
        self.agent_b  = VulnAgent()          # index 2
        self.agent_c  = ImpactAgent()        # index 3
        self.agent_c2 = ImpactAgent2()       # index 4  ← consensus pair for C
        self.agent_d  = RemediationAgent()   # index 5

        self.agents = [
            self.agent_a,
            self.agent_a2,
            self.agent_b,
            self.agent_c,
            self.agent_c2,
            self.agent_d,
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
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, self.analyze(threat, user_answers))
                return future.result()
        except RuntimeError:
            return asyncio.run(self.analyze(threat, user_answers))

    async def analyze(self, threat: str, user_answers: str = "") -> dict:
        """
        Full async pipeline.

        Returns dict with keys:
          status              : "rejected" | "needs_clarification" | "analyzed"
          original_input      : raw user input
          clean_threat        : enriched threat used for analysis (empty if rejected)
          validation          : full validator output dict
          agent_outputs       : list of agent dicts from all 6 agents
          final_report        : Judge's final synthesis
          disagreement_log    : dict with consensus comparison flags
        """
        loop = asyncio.get_running_loop()

        # ── Step 0: Validation ─────────────────────────────────────────────
        validation = await loop.run_in_executor(
            _EXECUTOR, self.validator.pass_one, threat
        )

        if validation["status"] == "Invalid":
            return {
                "status":           "rejected",
                "original_input":   threat,
                "clean_threat":     "",
                "validation":       validation,
                "agent_outputs":    [],
                "final_report":     "",
                "disagreement_log": {},
            }

        if validation["status"] == "Needs Clarification":
            if user_answers.strip():
                validation = await loop.run_in_executor(
                    _EXECUTOR,
                    lambda: self.validator.pass_two(threat, user_answers)
                )
            else:
                return {
                    "status":           "needs_clarification",
                    "original_input":   threat,
                    "clean_threat":     "",
                    "validation":       validation,
                    "questions":        validation["questions"],
                    "agent_outputs":    [],
                    "final_report":     "",
                    "disagreement_log": {},
                }

        clean_threat = validation.get("enriched") or threat

        # ── Step 1: All 6 agents in parallel ──────────────────────────────
        agent_outputs = await self._run_agents_parallel(clean_threat, loop)

        # ── Step 2: Disagreement detection ────────────────────────────────
        out_a, out_a2, out_b, out_c, out_c2, out_d = agent_outputs

        classification_disagree = _agents_disagree_category(out_a, out_a2)
        severity_disagree       = _agents_disagree_severity(out_c, out_c2)

        disagreement_log: dict = {
            "classification": {
                "agent_a_primary":   _extract_category(out_a["output"]),
                "agent_a_secondary": _extract_category(out_a2["output"]),
                "disagree":          classification_disagree,
            },
            "severity": {
                "agent_c_primary":   _extract_severity(out_c["output"]),
                "agent_c_secondary": _extract_severity(out_c2["output"]),
                "disagree":          severity_disagree,
            },
        }

        # ── Step 3: Judge synthesizes all outputs → final report ──────────
        final_report = await loop.run_in_executor(
            _EXECUTOR,
            lambda: self.judge.synthesize(
                clean_threat, agent_outputs, disagreement_log=disagreement_log
            )
        )

        return {
            "status":           "analyzed",
            "original_input":   threat,
            "clean_threat":     clean_threat,
            "validation":       validation,
            "agent_outputs":    agent_outputs,
            "final_report":     final_report["output"],
            "disagreement_log": disagreement_log,
        }

    # ── Internal helpers ───────────────────────────────────────────────────

    async def _run_agents_parallel(self, threat_input: str, loop) -> list:
        """
        Run all 6 specialist agents concurrently (A, A₂, B, C, C₂, D).
        Each agent's blocking .analyze() call runs in its own thread.
        Returns list of agent output dicts in agent order.
        Wall-clock time: ~5–10 sec (vs ~20–30 sec sequential).
        """
        tasks = [
            loop.run_in_executor(_EXECUTOR, agent.analyze, threat_input)
            for agent in self.agents
        ]
        return list(await asyncio.gather(*tasks))

    async def _run_agents_sequential(self, threat_input: str, loop) -> list:
        """
        LEGACY: Run all agents sequentially (one at a time).
        Only use if GPU has <16GB VRAM.
        Wall-clock time: ~20–30 sec per threat.
        """
        outputs = []
        for agent in self.agents:
            output = await loop.run_in_executor(_EXECUTOR, agent.analyze, threat_input)
            outputs.append(output)
        return outputs
