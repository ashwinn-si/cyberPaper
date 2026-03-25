import os
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_C_PROVIDER


class ImpactAgent(BaseAgent):
    """
    Agent C — Impact Assessor.

    Scores real-world damage potential and recommends immediate actions. Outputs:
      - SEVERITY SCORE (1–10 with anchored scale)
      - AFFECTED SCOPE (Individual → National Infrastructure)
      - POTENTIAL IMPACT (all applicable categories)
      - TOP 3 IMMEDIATE ACTIONS (priority-ordered direct instructions)

    Provider is injected from config — never hardcoded here.
    """

    def __init__(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_c.txt")
        super().__init__(
            name="Impact Assessor",
            system_prompt=self.load_prompt(prompt_path),
            provider=AGENT_C_PROVIDER
        )
