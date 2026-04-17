from abc import ABC, abstractmethod
from providers.base_provider import BaseLLMProvider


class BaseAgent(ABC):
    """
    Abstract base for all council agents.

    Agents never import a specific LLM library — they only interact with
    BaseLLMProvider. This makes the provider swap fully transparent to the
    agent layer: swap providers in config, agents are unchanged.
    """

    def __init__(self, name: str, system_prompt: str, provider: BaseLLMProvider):
        self.name          = name
        self.system_prompt = system_prompt
        self.provider      = provider

    def analyze(self, threat: str) -> dict:
        """
        Run this agent's analysis on a threat description.

        Returns a dict with:
            agent    : agent name (for judge traceability)
            provider : provider label (for ablation logging)
            output   : raw LLM response text
        """
        output = self.provider.complete(
            system_prompt=self.system_prompt,
            user_message=threat
        )
        return {
            "agent":    self.name,
            "provider": self.provider.provider_name(),
            "output":   output
        }

    @staticmethod
    def load_prompt(path: str) -> str:
        """Load a system prompt from a .txt file — avoids inline prompt strings."""
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
