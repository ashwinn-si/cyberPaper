import os
from providers.base_provider import BaseLLMProvider

class LlamaProvider(BaseLLMProvider):
    """
    Ollama Llama 3 provider (production-ready, generic, message-based, robust).
    - Base URL: http://localhost:11434
    - Endpoint: /api/chat
    - Model: llama3 (default)
    - Message-based chat format
    - Streaming disabled
    - Clean error handling
    - Compatible with requests, fetch, or axios (Python default: requests)
    """
    def __init__(self, model_name: str = None, api_base: str = None, max_tokens: int = 600, num_ctx: int = 2048, http_client=None):
        self.model_name = model_name or os.getenv("LLAMA_MODEL", "llama3")
        self.api_base = api_base or os.getenv("LLAMA_API_BASE", "http://localhost:11434")
        self.max_tokens = max_tokens   # max output tokens
        self.num_ctx = num_ctx         # context window (input + output); must be > prompt length
        self.http_client = http_client  # Optionally inject a custom HTTP client (requests/fetch/axios)

    def complete(self, system_prompt: str, user_message: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message}
            ],
            "stream": False,
            "options": {
                "num_ctx":    self.num_ctx,    # context window — must fit full prompt
                "num_predict": self.max_tokens  # max tokens to generate in response
            }
        }
        url = f"{self.api_base}/api/chat"

        # Use injected HTTP client if provided, else use requests
        client = self.http_client
        if client is not None:
            # Assume fetch/axios style: client(url, options)
            try:
                resp = client(url, {
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"},
                    "body": payload
                })
                if hasattr(resp, 'json'):
                    data = resp.json()
                else:
                    import json as _json
                    data = _json.loads(resp.text)
            except Exception as e:
                raise RuntimeError(f"Ollama (LlamaProvider) HTTP error: {e}")
        else:
            # Default: requests
            import requests
            try:
                response = requests.post(url, json=payload, timeout=300)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                raise RuntimeError(f"Ollama (LlamaProvider) HTTP error: {e}")
            except Exception as e:
                raise RuntimeError(f"Ollama (LlamaProvider) unexpected error: {e}")

        # Ollama returns {'message': {'role': 'assistant', 'content': ...}, ...}
        if not data or "message" not in data or "content" not in data["message"]:
            raise RuntimeError(f"Ollama (LlamaProvider) invalid response: {data}")
        return data["message"]["content"].strip()

    def provider_name(self) -> str:
        return f"Ollama Llama ({self.model_name})"
