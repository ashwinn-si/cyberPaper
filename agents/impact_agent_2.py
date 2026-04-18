import os
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_C_2_PROVIDER


class ImpactAgent2(BaseAgent):
    """
    Agent C₂ — Impact Assessor (secondary / consensus).

    Uses the same prompt as ImpactAgent but a different provider.
    Disagreements between C and C₂ are logged by the orchestrator and
    passed to the judge for explicit contradiction resolution.
    """

    def __init__(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_c.txt")
        super().__init__(
            name="Impact Assessor-2",
            system_prompt=self.load_prompt(prompt_path),
            provider=AGENT_C_2_PROVIDER
        )
