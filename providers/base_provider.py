from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """
    Abstract interface for all LLM providers.

    Any new provider (Gemini, Mistral, etc.) must implement this interface.
    Agents depend ONLY on this class — never on Claude or OpenAI directly.
    This is the key abstraction enabling per-agent provider swapping from config.
    """

    @abstractmethod
    def complete(self, system_prompt: str, user_message: str) -> str:
        """
        Send a prompt to the LLM and return the text response.

        Args:
            system_prompt : The agent's role/persona instructions.
            user_message  : The actual threat or judge input.

        Returns:
            The LLM's response as a plain string.
        """
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """
        Return a human-readable label for logging and judge synthesis traceability.

        Example: 'Claude (claude-sonnet-4-20250514)' or 'OpenAI (gpt-4o)'
        """
        pass
