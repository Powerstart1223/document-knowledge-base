"""Bridge the existing project DocumentGenerator to local HF or Ollama backends.

This keeps your current prompt-building pipeline and swaps only the backend.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from document_generator import DOCUMENT_TYPES, DocumentGenerator  # noqa: E402
from llm_backend import LLMBackend  # noqa: E402


class LocalHFBackend:
    """Drop-in replacement for llm_backend.LLMBackend using local transformers."""

    def __init__(self, model_path: str, default_max_tokens: int = 2048):
        self.model_path = model_path
        self.default_max_tokens = default_max_tokens

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)
        except Exception as exc:
            raise ValueError(
                "Could not load a tokenizer from model_path. Provide a local Hugging Face "
                "model directory that includes tokenizer files (for example "
                "tokenizer.json/tokenizer_config.json)."
            ) from exc

        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.model.eval()

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _render_messages(self, messages: list[dict]) -> str:
        if hasattr(self.tokenizer, "apply_chat_template"):
            try:
                return self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass

        parts = []
        for message in messages:
            role = message.get("role", "user").upper()
            content = message.get("content", "")
            parts.append(f"[{role}]\n{content}")
        parts.append("[ASSISTANT]\n")
        return "\n\n".join(parts)

    def _generate_from_prompt(self, prompt: str, temperature: float, max_tokens: int) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=temperature > 0,
                temperature=max(temperature, 1e-5),
                top_p=0.95,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        prompt_len = inputs["input_ids"].shape[1]
        new_tokens = output_ids[0][prompt_len:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
        prompt = self._render_messages(messages)
        return self._generate_from_prompt(prompt, temperature, max_tokens)

    def generate_document(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=min(max_tokens, self.default_max_tokens),
        )


def build_sample_params(document_type: str) -> dict:
    """Create minimal non-empty values for required document fields."""
    doc_def = DOCUMENT_TYPES[document_type]
    params = {}
    for field in doc_def.get("fields", []):
        key = field.get("key", "")
        label = field.get("label", key)
        params[key] = f"Sample {label}"

    params["style_reference_excerpt"] = "Use concise legal drafting with numbered sections."
    params["style_reference_name"] = "Default Internal Style"
    return params


def make_backend(
    provider: str,
    hf_model_path: str | None,
    ollama_model: str,
    ollama_base_url: str,
):
    provider = provider.lower().strip()
    if provider == "hf":
        if not hf_model_path:
            raise ValueError("--model-path is required when --provider hf")
        return LocalHFBackend(model_path=hf_model_path)

    if provider == "ollama":
        return LLMBackend(provider="ollama", model=ollama_model, base_url=ollama_base_url, api_key="ollama")

    raise ValueError("Unsupported provider. Use 'hf' or 'ollama'.")


def resolve_document_type(document_type: str | None) -> str:
    if not DOCUMENT_TYPES:
        raise ValueError("DOCUMENT_TYPES is empty.")

    if document_type is None:
        return next(iter(DOCUMENT_TYPES.keys()))

    if document_type not in DOCUMENT_TYPES:
        valid = ", ".join(sorted(DOCUMENT_TYPES.keys()))
        raise ValueError(f"Invalid --document-type '{document_type}'. Valid values: {valid}")

    return document_type


def run_once(
    provider: str,
    model_path: str | None,
    ollama_model: str,
    ollama_base_url: str,
    document_type: str | None = None,
) -> str:
    backend = make_backend(
        provider=provider,
        hf_model_path=model_path,
        ollama_model=ollama_model,
        ollama_base_url=ollama_base_url,
    )
    generator = DocumentGenerator(llm=backend)

    chosen_type = resolve_document_type(document_type)
    params = build_sample_params(chosen_type)
    return generator.generate(chosen_type, params, use_sec=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run project DocumentGenerator with local HF or Ollama backend")
    parser.add_argument("--provider", choices=["hf", "ollama"], default="ollama")
    parser.add_argument("--model-path", default=None, help="Local HF model directory (required for --provider hf)")
    parser.add_argument("--ollama-model", default="llama3.1:8b", help="Ollama model name (for --provider ollama)")
    parser.add_argument("--ollama-base-url", default="http://localhost:11434/v1", help="Ollama OpenAI-compatible base URL")
    parser.add_argument("--document-type", default=None, help="Key from DOCUMENT_TYPES")
    args = parser.parse_args()

    text = run_once(
        provider=args.provider,
        model_path=args.model_path,
        ollama_model=args.ollama_model,
        ollama_base_url=args.ollama_base_url,
        document_type=args.document_type,
    )
    print(text)