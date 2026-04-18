import os
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_A_2_PROVIDER


class ClassifierAgent2(BaseAgent):
    """
    Agent A₂ — Threat Classifier (secondary / consensus).

    Uses the same prompt as ClassifierAgent but a different provider.
    Disagreements between A and A₂ are logged by the orchestrator and
    passed to the judge for explicit contradiction resolution.
    """

    def __init__(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_a.txt")
        super().__init__(
            name="Threat Classifier-2",
            system_prompt=self.load_prompt(prompt_path),
            provider=AGENT_A_2_PROVIDER
        )
