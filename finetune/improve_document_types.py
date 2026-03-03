"""Discover and append new document types for the generator from corpus data.

Usage:
    python improve_document_types.py --corpus-dir finetune_output/corpus
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from llm_backend import LLMBackend


DOC_TYPES_FILE = PROJECT_ROOT / "document_types_generated.json"

TYPE_HINT_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z/&\-\s]{3,80}\s(?:Agreement|Amendment|Policy|Plan|Notice|Letter|Resolution|Term Sheet|Bylaws|Minutes))\b"
)


def _clean_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name or "").strip(" .,:;")
    return name.title()


def _text_files(corpus_dir: Path) -> list[Path]:
    return [p for p in corpus_dir.rglob("*.txt") if p.is_file()]


def discover_candidates(corpus_dir: Path, min_occurrences: int) -> list[str]:
    counts: Counter[str] = Counter()
    for path in _text_files(corpus_dir):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        header = text[:2500]
        for raw in TYPE_HINT_PATTERN.findall(header):
            name = _clean_name(raw)
            if len(name) >= 6:
                counts[name] += 1
    return [name for name, c in counts.most_common() if c >= min_occurrences]


def load_existing_names() -> set[str]:
    if not DOC_TYPES_FILE.exists():
        return set()
    data = json.loads(DOC_TYPES_FILE.read_text(encoding="utf-8"))
    return {str(item.get("name", "")).strip().lower() for item in data if isinstance(item, dict)}


def generate_fields(llm: LLMBackend, doc_type_name: str, guidance: str = "") -> list[dict]:
    guidance_block = f"\nGuidance to follow: {guidance.strip()}" if guidance.strip() else ""
    prompt = f"""Return ONLY a JSON array of 8-16 fields for drafting a "{doc_type_name}".
Each field object must include:
- key (snake_case)
- label
- type (text|date|textarea|number)
- placeholder
- help
No markdown, no explanations.{guidance_block}"""
    messages = [
        {"role": "system", "content": "You are a legal forms architect. Return valid JSON only."},
        {"role": "user", "content": prompt},
    ]
    raw = llm.chat(messages, temperature=0.1, max_tokens=2200)
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start < 0 or end <= start:
        return []
    try:
        data = json.loads(raw[start:end])
    except Exception:
        return []

    out = []
    for f in data:
        if not isinstance(f, dict):
            continue
        key = re.sub(r"[^a-z0-9_]+", "_", str(f.get("key", "")).strip().lower()).strip("_")
        label = str(f.get("label", "")).strip()
        ftype = str(f.get("type", "text")).strip().lower()
        if ftype not in {"text", "date", "textarea", "number"}:
            ftype = "text"
        if not key or not label:
            continue
        out.append(
            {
                "key": key,
                "label": label,
                "type": ftype,
                "placeholder": str(f.get("placeholder", "")).strip(),
                "help": str(f.get("help", "")).strip() or f"Enter {label.lower()}",
                "section": "Auto",
            }
        )
    return out[:20]


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-discover and add new document types")
    parser.add_argument("--corpus-dir", default=str(PROJECT_ROOT / "finetune_output" / "corpus"))
    parser.add_argument("--min-occurrences", type=int, default=2)
    parser.add_argument("--max-new-types", type=int, default=12)
    parser.add_argument("--provider", default=__import__("os").getenv("LLM_PROVIDER", "ollama"))
    parser.add_argument("--model", default=__import__("os").getenv("OLLAMA_MODEL", __import__("os").getenv("OPENAI_MODEL", "llama3.1:8b")))
    parser.add_argument("--base-url", default=__import__("os").getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"))
    parser.add_argument("--api-key", default=__import__("os").getenv("OPENAI_API_KEY", "ollama"))
    parser.add_argument("--guidance", default="", help="Extra guidance for how discovered templates should be structured")
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    corpus_dir.mkdir(parents=True, exist_ok=True)

    discovered = discover_candidates(corpus_dir, min_occurrences=args.min_occurrences)
    existing = load_existing_names()
    new_candidates = [x for x in discovered if x.lower() not in existing][: args.max_new_types]

    if not new_candidates:
        print("No new document types discovered.")
        return

    llm = LLMBackend(provider=args.provider, model=args.model, base_url=args.base_url, api_key=args.api_key)

    current = []
    if DOC_TYPES_FILE.exists():
        current = json.loads(DOC_TYPES_FILE.read_text(encoding="utf-8"))

    added = 0
    for name in new_candidates:
        fields = generate_fields(llm, name, guidance=args.guidance)
        if not fields:
            continue
        current.append(
            {
                "name": name,
                "description": f"Auto-discovered template generated from your corpus: {name}.",
                "icon": "AI",
                "category": "Auto-Discovered",
                "fields": fields,
            }
        )
        added += 1

    DOC_TYPES_FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")
    print(f"Added {added} new document types to {DOC_TYPES_FILE}")


if __name__ == "__main__":
    main()
