from providers.llama_provider import LlamaProvider


class FoundationSecProvider(LlamaProvider):
    """
    Foundation-Sec-8B-Instruct via Ollama.
    Specialized for threat detection with 98% phishing recall.
    """

    def __init__(self, api_base: str = None):
        super().__init__(
            model_name="foundation-sec-8b-instruct",
            api_base=api_base,
        )

    def provider_name(self) -> str:
        return "Foundation-Sec-8B-Instruct (Ollama)"
