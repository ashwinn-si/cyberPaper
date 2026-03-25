from agents.classifier_agent import ClassifierAgent
from agents.vuln_agent import VulnAgent
from agents.impact_agent import ImpactAgent
from agents.judge_agent import JudgeAgent


class CyberCouncil:
    """
    Orchestrates all council agents and the judge synthesizer.

    Workflow:
      1. Each of the 3 specialist agents independently analyzes the threat.
      2. The Judge reads all 3 outputs and produces one authoritative report.

    The council never imports any LLM SDK — all model access is encapsulated
    in provider files, injected via config/agent_config.py.
    """

    def __init__(self):
        self.agents = [
            ClassifierAgent(),
            VulnAgent(),
            ImpactAgent(),
        ]
        self.judge = JudgeAgent()

    def analyze(self, threat: str) -> dict:
        """
        Run the full council analysis pipeline on a threat description.

        Returns:
            threat        : the original threat text
            agent_outputs : list of dicts from each specialist agent
            final_report  : the judge's synthesized authoritative output
        """
        # Step 1 — All 3 agents analyze independently (sequential for clarity;
        #           could be parallelized with concurrent.futures for speed)
        agent_outputs = [agent.analyze(threat) for agent in self.agents]

        # Step 2 — Judge synthesizes all outputs into one report
        final = self.judge.synthesize(threat, agent_outputs)

        return {
            "threat":        threat,
            "agent_outputs": agent_outputs,
            "final_report":  final["output"]
        }
