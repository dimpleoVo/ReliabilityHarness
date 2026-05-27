"""
Minimal LLM client for generation-only candidate generation (DeepSeek API).

Design rules:
  - No module-level API key reading.
  - No module-level HTTP client initialization.
  - No import-time side effects.
  - load_dotenv() is called ONLY inside LLMClient.from_env(), with an explicit
    path (REPO_ROOT / ".env") to avoid find_dotenv() AssertionError in stdin
    or non-file execution contexts.
  - Tests use a mock client — they never call from_env().
  - Artifacts record model_name only, never API key or base_url.

Environment variables read by from_env():
  DEEPSEEK_API_KEY   — required; raises RuntimeError if absent
  DEEPSEEK_BASE_URL  — optional; default https://api.deepseek.com
  DEEPSEEK_MODEL     — optional; default deepseek-v4-flash
"""
from __future__ import annotations


class LLMClient:
    """Thin HTTP wrapper around the DeepSeek chat completions API."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "deepseek-v4-flash",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        base_url: str = "https://api.deepseek.com",
    ) -> None:
        self._api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._base_url = base_url.rstrip("/")

    @classmethod
    def from_env(
        cls,
        model_name: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> "LLMClient":
        """Construct a client from environment / .env file.

        Calls load_dotenv() with the explicit repo-root .env path so this works
        reliably in all execution contexts (module run, stdin pipe, subprocess).
        Never called at module import time — only when generation mode is active.

        Parameters
        ----------
        model_name:
            Override model name. Falls back to DEEPSEEK_MODEL env var, then
            "deepseek-v4-flash".
        temperature:
            Sampling temperature (default 0.0).
        max_tokens:
            Max tokens per generation (default 1024).

        Raises
        ------
        RuntimeError
            If DEEPSEEK_API_KEY is missing or empty.
        """
        import os
        from dotenv import load_dotenv
        from reliability_harness.utils.paths import REPO_ROOT

        env_path = REPO_ROOT / ".env"
        load_dotenv(env_path)

        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is required for generation mode. "
                "Set it in .env (copy from .env.example) or as an environment variable."
            )

        base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
        resolved_model = (
            model_name
            or os.environ.get("DEEPSEEK_MODEL", "").strip()
            or "deepseek-v4-flash"
        )

        return cls(
            api_key=api_key,
            model_name=resolved_model,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url=base_url,
        )

    def generate(self, prompt: str) -> str:
        """Send prompt to the LLM and return the raw text response."""
        import requests

        url = self._base_url + "/chat/completions"
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
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
