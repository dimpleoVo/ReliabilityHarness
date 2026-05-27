"""
Minimal LLM client for generation-only candidate generation (DeepSeek API).

Design rules:
  - No module-level API key reading.
  - No module-level HTTP client initialization.
  - No import-time side effects.
  - load_dotenv() is called ONLY inside LLMClient.from_env().
  - Tests use a mock client — they never call from_env().
  - Artifacts record model_name only, never API key.
"""
from __future__ import annotations


class LLMClient:
    """Thin HTTP wrapper around the DeepSeek chat completions API."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "deepseek-chat",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        base_url: str = "https://api.deepseek.com/v1",
    ) -> None:
        self._api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._base_url = base_url.rstrip("/")

    @classmethod
    def from_env(
        cls,
        model_name: str = "deepseek-chat",
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> "LLMClient":
        """Construct a client from environment variables.

        Calls load_dotenv() here — never at module import time.
        Raises RuntimeError if DEEPSEEK_API_KEY is missing.
        """
        import os
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is required for generation mode. "
                "Set it in .env or as an environment variable."
            )
        return cls(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def generate(self, prompt: str) -> str:
        """Send prompt to the LLM and return the raw text response."""
        import requests

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        url = f"{self._base_url}/chat/completions"
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
