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
