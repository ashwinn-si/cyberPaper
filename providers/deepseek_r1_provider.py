from providers.llama_provider import LlamaProvider


class DeepSeekR1Provider(LlamaProvider):
    """
    DeepSeek-R1-Reasoning via Ollama.
    Risk quantification & business impact scoring with advanced reasoning.
    Used by ImpactAgent (Agent C) for severity scoring and impact assessment.
    """

    def __init__(self, api_base: str = None):
        super().__init__(
            model_name="deepseek-r1",
            api_base=api_base,
        )

    def provider_name(self) -> str:
        return "DeepSeek-R1-Reasoning (Ollama)"
