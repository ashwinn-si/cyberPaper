from providers.llama_provider import LlamaProvider


class LlamaFoundationAIProvider(LlamaProvider):
    """
    Llama-3.1-FoundationAI-SecurityLLM-8B via Ollama.
    Deep threat intelligence analysis; matches 70B performance.
    Used by ClassifierAgent (Agent A) for detailed threat classification.
    """

    def __init__(self, api_base: str = None):
        super().__init__(
            model_name="llama-3.1-foundationai-securityllm-8b",
            api_base=api_base,
        )

    def provider_name(self) -> str:
        return "Llama-3.1-FoundationAI-SecurityLLM-8B (Ollama)"
