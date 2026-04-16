from providers.llama_provider import LlamaProvider


class MistralNemoProvider(LlamaProvider):
    """
    Mistral-Nemo-Instruct via Ollama.
    Actionable SecOps workflows & containment steps.
    Used by RemediationAgent (Agent D) for remediation planning and recovery steps.
    """

    def __init__(self, api_base: str = None):
        super().__init__(
            model_name="mistral-nemo",
            api_base=api_base,
        )

    def provider_name(self) -> str:
        return "Mistral-Nemo-Instruct (Ollama)"
