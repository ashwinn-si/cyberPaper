import os
from openai import OpenAI
from dotenv import load_dotenv
from providers.base_provider import BaseLLMProvider

load_dotenv()


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI GPT provider.

    Default model : gpt-4o
    Override model: OpenAIProvider("gpt-4-turbo")

    Only this file imports the `openai` SDK.
    Agents and council code never touch this class directly.
    """

    def __init__(self, model_name: str = "gpt-4o", max_tokens: int = 600):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def complete(self, system_prompt: str, user_message: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message}
            ]
        )
        return response.choices[0].message.content

    def provider_name(self) -> str:
        return f"OpenAI ({self.model_name})"
