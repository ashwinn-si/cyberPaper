import os
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_B_PROVIDER


class VulnAgent(BaseAgent):
    """
    Agent B — Vulnerability Analyst.

    Maps the attack to CVE and MITRE ATT&CK frameworks. Outputs:
      - CVE STATUS (specific CVE ID or "No known CVE")
      - MITRE ATT&CK TACTIC (high-level attacker goal)
      - MITRE ATT&CK TECHNIQUE ID (e.g. T1566)
      - ATTACK CHAIN (2–3 step progression)
      - AFFECTED SYSTEMS (software/OS/services targeted)

    Provider is injected from config — never hardcoded here.
    """

    def __init__(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_b.txt")
        super().__init__(
            name="Vulnerability Analyst",
            system_prompt=self.load_prompt(prompt_path),
            provider=AGENT_B_PROVIDER
        )
