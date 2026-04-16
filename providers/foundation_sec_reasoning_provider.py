from providers.llama_provider import LlamaProvider


class FoundationSecReasoningProvider(LlamaProvider):
    """
    Foundation-Sec-8B-Reasoning via Ollama.
    Specialized for classification verification with multi-step reasoning.
    Used by ValidatorAgent for input validation.
    """

    def __init__(self, api_base: str = None):
        super().__init__(
            model_name="foundation-sec-8b-reasoning",
            api_base=api_base,
        )

    def provider_name(self) -> str:
        return "Foundation-Sec-8B-Reasoning (Ollama)"
