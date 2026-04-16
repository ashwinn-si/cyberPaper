from providers.llama_provider import LlamaProvider


class Gemma2SecurityProvider(LlamaProvider):
    """
    Gemma-2-27B-Security via Ollama.
    Code/log vulnerability scanning; lightweight exploit analysis.
    Used by VulnAgent (Agent B) for CVE mapping and MITRE ATT&CK analysis.
    """

    def __init__(self, api_base: str = None):
        super().__init__(
            model_name="gemma-2-27b-security",
            api_base=api_base,
        )

    def provider_name(self) -> str:
        return "Gemma-2-27B-Security (Ollama)"
