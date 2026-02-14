"""
LLM Backend — Ollama / OpenAI wrapper using the openai>=1.0 client library.

Ollama exposes an OpenAI-compatible endpoint at http://localhost:11434/v1,
so the same OpenAI() client works for both providers with zero code changes.
"""

import os
import requests
from openai import OpenAI


class LLMBackend:
    """Unified interface for Ollama and OpenAI language models."""

    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
    ):
        self.provider = provider.lower()
        self.model = model

        if self.provider == "ollama":
            self.base_url = base_url
            self.api_key = api_key
            # Native Ollama API base (non-OpenAI) for health checks / model list
            self._ollama_native_url = base_url.replace("/v1", "")
        else:
            # OpenAI — use real key from env
            self.base_url = "https://api.openai.com/v1"
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion request and return the assistant text."""
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # Ollama supports extra_body for native parameters like num_ctx
        if self.provider == "ollama":
            kwargs["extra_body"] = {"num_ctx": 8192}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def generate_document(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a long-form document with a system + user prompt pair."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if self.provider == "ollama":
            kwargs["extra_body"] = {"num_ctx": 8192}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def is_available(self) -> bool:
        """Return True if the backend is reachable and has at least one model."""
        try:
            if self.provider == "ollama":
                r = requests.get(
                    f"{self._ollama_native_url}/api/tags", timeout=3
                )
                return r.status_code == 200
            else:
                # OpenAI — verify the key isn't empty and looks valid
                if not self.api_key or self.api_key == "ollama":
                    return False
                # Basic format check for OpenAI keys (starts with sk-)
                return self.api_key.startswith("sk-") and len(self.api_key) > 20
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """Return available model names from the backend."""
        try:
            if self.provider == "ollama":
                r = requests.get(
                    f"{self._ollama_native_url}/api/tags", timeout=5
                )
                r.raise_for_status()
                return [m["name"] for m in r.json().get("models", [])]
            else:
                models = self.client.models.list()
                return [m.id for m in models.data]
        except Exception:
            return []
