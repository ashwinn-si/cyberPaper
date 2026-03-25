import os
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_A_PROVIDER


class ClassifierAgent(BaseAgent):
    """
    Agent A — Threat Classifier.

    Identifies the threat type from a description and outputs:
      - THREAT CATEGORY (one of 9 canonical categories)
      - CONFIDENCE SCORE (0–100%)
      - JUSTIFICATION (one sentence referencing specific indicators)

    Provider is injected from config — never hardcoded here.
    """

    def __init__(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_a.txt")
        super().__init__(
            name="Threat Classifier",
            system_prompt=self.load_prompt(prompt_path),
            provider=AGENT_A_PROVIDER
        )
