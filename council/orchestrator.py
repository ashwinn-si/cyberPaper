"""
CyberCouncil Orchestrator
─────────────────────────
Flow:
  1. ValidatorAgent (Agent 0) — validates and enriches raw input (1–2 passes)
  2. Agents A, B, C, D       — run SEQUENTIALLY on the enriched threat (Round 1)
     (Sequential execution for GPU memory safety on 16GB VRAM)
  3. JudgeAgent              — synthesizes Round 1 outputs → draft report
  4. Agents A, B, C, D       — run SEQUENTIALLY with draft report as context (Round 2)
  5. JudgeAgent              — synthesizes Round 2 outputs → final report

Sequential execution (one agent at a time) ensures GPU memory stays under 16GB.
Each agent unloads before the next runs. Wall-clock time ~20–30 sec per threat
vs ~5–10 sec with parallel execution (not feasible with 16GB GPU).

For production with 24GB+ GPU, switch _run_agents_sequential to _run_agents_parallel.
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

        # ── Step 1: Round 1 — all agents sequentially ──────────────────────
        round1_outputs = await self._run_agents_sequential(clean_threat, loop)

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
        round2_outputs = await self._run_agents_sequential(round2_input, loop)

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

    async def _run_agents_sequential(self, threat_input: str, loop) -> list:
        """
        Run all 4 specialist agents sequentially (one at a time).
        Each agent unloads from GPU before the next one loads.
        Ensures GPU memory stays under 16GB VRAM.
        Returns list of agent output dicts in agent order (A, B, C, D).
        """
        outputs = []
        for agent in self.agents:
            output = await loop.run_in_executor(_EXECUTOR, agent.analyze, threat_input)
            outputs.append(output)
        return outputs

    async def _run_agents_parallel(self, threat_input: str, loop) -> list:
        """
        LEGACY: Run all 4 specialist agents concurrently.
        Only use if GPU has 24GB+ VRAM.
        Each agent's blocking .analyze() call runs in its own thread.
        Returns list of agent output dicts in agent order (A, B, C, D).
        """
        tasks = [
            loop.run_in_executor(_EXECUTOR, agent.analyze, threat_input)
            for agent in self.agents
        ]
        return list(await asyncio.gather(*tasks))
