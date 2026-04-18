import os
from agents.base_agent import BaseAgent
from config.agent_config import JUDGE_PROVIDER


class JudgeAgent(BaseAgent):
    """
    Judge Agent — CISO Synthesizer.

    Reads all specialist outputs and produces ONE authoritative threat
    assessment. Outputs:
      - FINAL CLASSIFICATION (confirm or correct Agent A / A₂)
      - FINAL CVE AND MITRE MAPPING (confirm or correct Agent B)
      - FINAL SEVERITY (confirm or adjust Agent C / C₂ score)
      - CONTRADICTION REPORT (agent conflicts and resolutions)
      - FINAL RESPONSE PLAN (priority-ordered actions)

    When called with disagreement_log and round_weights, these are appended
    to the judge's input so it can explicitly address consensus conflicts and
    give higher trust to agents that revised their position after seeing the
    draft report (indicative of active reasoning, not anchoring).
    """

    def __init__(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_judge.txt")
        super().__init__(
            name="Judge (CISO)",
            system_prompt=self.load_prompt(prompt_path),
            provider=JUDGE_PROVIDER
        )

    def synthesize(
        self,
        threat: str,
        agent_outputs: list,
        disagreement_log: dict | None = None,
        round_weights: dict | None = None,
    ) -> dict:
        """
        Build a combined input from all agent outputs and run the judge.

        Args:
            threat           : enriched threat description
            agent_outputs    : list of {agent, provider, output} dicts
            disagreement_log : consensus comparison results from orchestrator
            round_weights    : per-agent weight dict (1.5 if revised, 1.0 if stable)

        The judge message includes each agent's name, provider, and optional
        weight label so the judge can reason about cross-model agreement and
        deliberate position changes.
        """
        weight_map = round_weights or {}

        agent_sections = []
        for r in agent_outputs:
            weight_info = weight_map.get(r["agent"])
            weight_label = ""
            if weight_info:
                if weight_info["changed"]:
                    weight_label = " [REVISED POSITION — higher trust]"
                else:
                    weight_label = " [STABLE POSITION]"
            agent_sections.append(
                f"=== {r['agent']} (via {r['provider']}){weight_label} ===\n{r['output']}"
            )

        combined = "\n\n".join(agent_sections)
        judge_input = f"Original Threat:\n{threat}\n\n{combined}"

        # Append disagreement metadata as structured context for the judge
        if disagreement_log:
            cl = disagreement_log.get("classification", {})
            sv = disagreement_log.get("severity", {})
            lines = ["\n--- CONSENSUS ANALYSIS ---"]

            if cl.get("disagree"):
                lines.append(
                    f"CLASSIFICATION CONFLICT: Classifier-1={cl.get('agent_a_primary')} "
                    f"vs Classifier-2={cl.get('agent_a_secondary')} — you MUST resolve this."
                )
            else:
                lines.append(
                    f"CLASSIFICATION AGREEMENT: both classifiers agree on "
                    f"'{cl.get('agent_a_primary')}' — high confidence."
                )

            if sv.get("disagree"):
                lines.append(
                    f"SEVERITY CONFLICT: Impact-1={sv.get('agent_c_primary')} "
                    f"vs Impact-2={sv.get('agent_c_secondary')} — you MUST resolve this."
                )
            else:
                lines.append(
                    f"SEVERITY AGREEMENT: both impact agents agree on score "
                    f"{sv.get('agent_c_primary')} — high confidence."
                )

            judge_input += "\n".join(lines)

        return self.analyze(judge_input)
