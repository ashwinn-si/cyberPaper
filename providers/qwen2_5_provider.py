from providers.llama_provider import LlamaProvider


class Qwen25Provider(LlamaProvider):
    """
    Qwen2.5-72B-Instruct via Ollama.
    Structured reporting; resolves agent contradictions.
    Used by JudgeAgent for final synthesis and orchestration.
    """

    def __init__(self, api_base: str = None):
        super().__init__(
            model_name="qwen2.5",
            api_base=api_base,
        )

    def provider_name(self) -> str:
        return "Qwen2.5-72B-Instruct (Ollama)"
