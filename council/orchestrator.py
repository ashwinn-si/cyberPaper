"""
CyberCouncil Orchestrator
─────────────────────────
Flow:
  1. ValidatorAgent (Agent 0) — validates and enriches raw input (1–2 passes)
  2. Agents A, A₂, B, C, C₂, D — run IN PARALLEL on the enriched threat (Round 1)
  3. Disagreement detection — A vs A₂ (classification), C vs C₂ (severity)
  4. JudgeAgent              — synthesizes Round 1 outputs + disagreement log → draft report
  5. Agents A, A₂, B, C, C₂, D — run IN PARALLEL with draft report as context (Round 2)
  6. Round-change detection  — agents that revised their position get higher weight
  7. JudgeAgent              — synthesizes Round 2 outputs + weights + disagreements → final report

Parallel execution uses asyncio + ThreadPoolExecutor. All agents run concurrently.
Each agent's blocking API call runs in its own thread. GPU memory stays under 34GB.
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


def _agent_changed_position(r1: dict, r2: dict) -> bool:
    """
    True if an agent revised its core position between Round 1 and Round 2.
    Checks category change (classifiers) or severity shift >1 (impact agents).
    """
    # Try category first (classifier agents)
    c1 = _extract_category(r1["output"])
    c2 = _extract_category(r2["output"])
    if c1 is not None and c2 is not None:
        return c1 != c2
    # Fall back to severity (impact agents)
    s1 = _extract_severity(r1["output"])
    s2 = _extract_severity(r2["output"])
    if s1 is not None and s2 is not None:
        return abs(s1 - s2) > 1
    return False


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
          round1_outputs      : list of agent dicts from Round 1 (6 agents)
          draft_report        : Judge's Round 1 synthesis
          round2_outputs      : list of agent dicts from Round 2 (6 agents)
          final_report        : Judge's final synthesis
          disagreement_log    : dict with consensus comparison and round-change flags
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
                "round1_outputs":   [],
                "draft_report":     "",
                "round2_outputs":   [],
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
                    "round1_outputs":   [],
                    "draft_report":     "",
                    "round2_outputs":   [],
                    "final_report":     "",
                    "disagreement_log": {},
                }

        clean_threat = validation.get("enriched") or threat

        # ── Step 1: Round 1 — all agents in parallel ───────────────────────
        round1_outputs = await self._run_agents_parallel(clean_threat, loop)

        # ── Step 2: Disagreement detection (Round 1) ──────────────────────
        r1_a, r1_a2, r1_b, r1_c, r1_c2, r1_d = round1_outputs

        classification_disagree = _agents_disagree_category(r1_a, r1_a2)
        severity_disagree       = _agents_disagree_severity(r1_c, r1_c2)

        disagreement_log: dict = {
            "classification": {
                "agent_a_primary":   _extract_category(r1_a["output"]),
                "agent_a_secondary": _extract_category(r1_a2["output"]),
                "disagree":          classification_disagree,
            },
            "severity": {
                "agent_c_primary":   _extract_severity(r1_c["output"]),
                "agent_c_secondary": _extract_severity(r1_c2["output"]),
                "disagree":          severity_disagree,
            },
            "round_changes": {},   # filled after Round 2
        }

        # ── Step 3: Judge synthesizes Round 1 ─────────────────────────────
        draft_report = await loop.run_in_executor(
            _EXECUTOR,
            lambda: self.judge.synthesize(
                clean_threat, round1_outputs, disagreement_log=disagreement_log
            )
        )

        # ── Step 4: Round 2 — agents re-analyze with draft context ────────
        round2_input = (
            f"{clean_threat}\n\n"
            f"--- JUDGE DRAFT REPORT (Round 1) ---\n{draft_report['output']}"
        )
        round2_outputs = await self._run_agents_parallel(round2_input, loop)

        # ── Step 5: Round-change detection (position revision weighting) ──
        round_changes = {}
        for r1, r2 in zip(round1_outputs, round2_outputs):
            changed = _agent_changed_position(r1, r2)
            round_changes[r2["agent"]] = {
                "changed":  changed,
                "weight":   1.5 if changed else 1.0,
            }
        disagreement_log["round_changes"] = round_changes

        # ── Step 6: Judge synthesizes Round 2 → final report ──────────────
        final_report = await loop.run_in_executor(
            _EXECUTOR,
            lambda: self.judge.synthesize(
                clean_threat, round2_outputs,
                disagreement_log=disagreement_log,
                round_weights=round_changes,
            )
        )

        return {
            "status":           "analyzed",
            "original_input":   threat,
            "clean_threat":     clean_threat,
            "validation":       validation,
            "round1_outputs":   round1_outputs,
            "draft_report":     draft_report["output"],
            "round2_outputs":   round2_outputs,
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
