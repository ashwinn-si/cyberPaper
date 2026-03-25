import os
import anthropic
from dotenv import load_dotenv
from providers.base_provider import BaseLLMProvider

load_dotenv()


class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude provider.

    Default model : claude-sonnet-4-20250514
    Override model: ClaudeProvider("claude-opus-4-5")

    Only this file imports the `anthropic` SDK.
    Agents and council code never touch this class directly.
    """

    def __init__(self, model_name: str = "claude-sonnet-4-20250514", max_tokens: int = 600):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def complete(self, system_prompt: str, user_message: str) -> str:
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text

    def provider_name(self) -> str:
        return f"Claude ({self.model_name})"
