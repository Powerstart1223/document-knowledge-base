"""Evaluate an Ollama model against a fixed regression set."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run_ollama(model_name: str, prompt: str, timeout_seconds: int) -> str:
    result = subprocess.run(
        ["ollama", "run", model_name, prompt],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "ollama run failed").strip())
    return (result.stdout or "").strip()


def score_case(response: str, required_phrases: list[str]) -> float:
    if not required_phrases:
        return 1.0
    hay = response.lower()
    hits = sum(1 for phrase in required_phrases if phrase.lower() in hay)
    return hits / max(1, len(required_phrases))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate an Ollama model on a fixed regression set")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--eval-set", default=str(Path(__file__).resolve().parent / "regression_eval_set.json"))
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--output-file", default="")
    args = parser.parse_args()

    eval_set_path = Path(args.eval_set)
    if not eval_set_path.exists():
        raise SystemExit(f"Eval set not found: {eval_set_path}")

    payload = json.loads(eval_set_path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise SystemExit("Eval set has no cases.")

    results: list[dict] = []
    passes = 0
    for case in cases:
        if not isinstance(case, dict):
            continue
        prompt = str(case.get("prompt", "")).strip()
        required = [str(x).strip() for x in case.get("required_phrases", []) if str(x).strip()]
        min_case_score = float(case.get("min_case_score", 0.5))
        case_id = str(case.get("id", "case"))
        if not prompt:
            continue
        try:
            response = run_ollama(args.model_name, prompt, args.timeout_seconds)
            case_score = score_case(response, required)
            case_pass = case_score >= min_case_score
        except Exception as exc:
            response = f"ERROR: {exc}"
            case_score = 0.0
            case_pass = False

        if case_pass:
            passes += 1
        results.append(
            {
                "id": case_id,
                "min_case_score": min_case_score,
                "score": case_score,
                "pass": case_pass,
                "required_phrases": required,
                "response_preview": response[:400],
            }
        )

    total = len(results)
    pass_rate = passes / max(1, total)
    summary = {
        "model_name": args.model_name,
        "eval_set": str(eval_set_path),
        "cases_total": total,
        "cases_passed": passes,
        "pass_rate": pass_rate,
        "results": results,
    }

    text = json.dumps(summary, indent=2)
    if args.output_file:
        Path(args.output_file).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
