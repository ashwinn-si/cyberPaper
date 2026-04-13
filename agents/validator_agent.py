import re
from agents.base_agent import BaseAgent
from config.agent_config import AGENT_VALIDATOR_PROVIDER


class ValidatorAgent(BaseAgent):
    """
    Agent 0 — Threat Validator and Preprocessor.

    Operates in two passes:
      Pass 1 (first_pass=True)  : evaluates raw input, may ask questions or pass directly
      Pass 2 (first_pass=False) : merges original input + user answers, always passes

    The council calls pass_one() first. If questions are returned, the council
    collects user answers and calls pass_two(). After pass_two(), the enriched
    threat goes to Agents A, B, C, D. No third pass ever occurs.
    """

    def __init__(self):
        super().__init__(
            name="Validator",
            system_prompt=self.load_prompt("prompts/prompt_validator.txt"),
            provider=AGENT_VALIDATOR_PROVIDER
        )

    def pass_one(self, raw_input: str) -> dict:
        """
        First pass: evaluate raw user input.

        Returns dict with keys:
          status  : "Invalid" | "Needs Clarification" | "Pass"
          output  : full raw LLM output
          questions : list[str] if status == "Needs Clarification", else []
          enriched  : str if status == "Pass", else ""
        """
        result = self.analyze(raw_input)
        return self._parse_output(result["output"])

    def pass_two(self, raw_input: str, user_answers: str) -> dict:
        """
        Second pass: merge original input + user answers into enriched threat.
        Always returns status == "Pass".

        Args:
            raw_input    : the original user-submitted threat description
            user_answers : the user's answers to the clarifying questions
        """
        combined = (
            f"ORIGINAL INPUT:\n{raw_input}\n\n"
            f"USER'S ANSWERS TO CLARIFYING QUESTIONS:\n{user_answers}\n\n"
            f"This is the second pass. You must output STATUS: Pass and an ENRICHED THREAT."
        )
        result = self.analyze(combined)
        parsed = self._parse_output(result["output"])
        # Hard enforce Pass on second pass regardless of model output
        parsed["status"] = "Pass"
        return parsed

    def _parse_output(self, text: str) -> dict:
        """Parse structured LLM output into a clean dict."""
        status_match = re.search(r"STATUS:\s*(Invalid|Needs Clarification|Pass)", text, re.IGNORECASE)
        status = status_match.group(1).strip() if status_match else "Pass"

        questions = []
        if status == "Needs Clarification":
            q_matches = re.findall(r"^\s*\d+\.\s+(.+)$", text, re.MULTILINE)
            questions = [q.strip() for q in q_matches if q.strip()]

        enriched = ""
        enriched_match = re.search(r"ENRICHED THREAT:\s*(.+?)(?:\n\n|\Z)", text, re.DOTALL)
        if enriched_match:
            enriched = enriched_match.group(1).strip()

        reason = ""
        reason_match = re.search(r"REASON:\s*(.+?)(?:\n|$)", text)
        if reason_match:
            reason = reason_match.group(1).strip()

        return {
            "status":    status,
            "output":    text,
            "questions": questions,
            "enriched":  enriched,
            "reason":    reason,
        }
