import os
from agents.base_agent import BaseAgent
from config.agent_config import JUDGE_PROVIDER


class JudgeAgent(BaseAgent):
    """
    Judge Agent — CISO Synthesizer.

    Reads all three specialist outputs and produces ONE authoritative threat
    assessment. Outputs:
      - FINAL CLASSIFICATION (confirm or correct Agent A)
      - FINAL CVE AND MITRE MAPPING (confirm or correct Agent B)
      - FINAL SEVERITY (confirm or adjust Agent C's score)
      - CONTRADICTION REPORT (list conflicts between agents and resolutions)
      - FINAL RESPONSE PLAN (priority-ordered actions, expanded from Agent C)

    The contradiction report is the novel architectural contribution that
    differentiates this system from a simple ensemble.
    """

    def __init__(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_judge.txt")
        super().__init__(
            name="Judge (CISO)",
            system_prompt=self.load_prompt(prompt_path),
            provider=JUDGE_PROVIDER
        )

    def synthesize(self, threat: str, agent_outputs: list) -> dict:
        """
        Build a combined input from all agent outputs and run the judge.

        The judge message includes each agent's name AND provider label so the
        judge is aware of which model produced which analysis — this enables
        cross-model ablation traceability in paper reporting.
        """
        combined = "\n\n".join(
            f"=== {r['agent']} (via {r['provider']}) ===\n{r['output']}"
            for r in agent_outputs
        )
        judge_input = f"Original Threat:\n{threat}\n\n{combined}"
        return self.analyze(judge_input)
