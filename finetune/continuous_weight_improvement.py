"""End-to-end continuous weight-improvement pipeline for Ollama.

Pipeline:
1) Build corpus from uploads + EDGAR
2) Build training JSONL
3) Fine-tune LoRA
4) Export/register model in Ollama
5) Improve generated document types from discovered corpus types

Usage:
    python continuous_weight_improvement.py --include-uploads --include-edgar
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config import OLLAMA_MODEL_NAME

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FINETUNE_DIR = PROJECT_ROOT / "finetune"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"\n[RUN] {' '.join(shlex.quote(x) for x in cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd or PROJECT_ROOT), text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")


def run_capture(cmd: list[str], cwd: Path | None = None) -> str:
    print(f"\n[RUN] {' '.join(shlex.quote(x) for x in cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd or PROJECT_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "").strip() or f"Command failed: {' '.join(cmd)}")
    return result.stdout


def _safe_read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuous fine-tune + export + doc-type improvement pipeline")
    parser.add_argument("--include-uploads", action="store_true")
    parser.add_argument("--include-edgar", action="store_true")
    parser.add_argument("--skip-corpus-build", action="store_true")
    parser.add_argument("--skip-doc-type-improvement", action="store_true")
    parser.add_argument("--skip-export", action="store_true")
    parser.add_argument("--fallback", action="store_true", help="Use fallback train settings (lower memory)")
    parser.add_argument("--max-upload-files", type=int, default=250)
    parser.add_argument("--max-filings-per-query", type=int, default=10)
    parser.add_argument("--max-chars-per-doc", type=int, default=20000)
    parser.add_argument(
        "--edgar-queries",
        default="material agreement,credit agreement,merger agreement,employment agreement,risk factors",
    )
    parser.add_argument("--sec-user-agent", default="")
    parser.add_argument("--corpus-dir", default=str(PROJECT_ROOT / "finetune_output" / "corpus"))
    parser.add_argument(
        "--doc-type-guidance",
        default="",
        help="Guidance prompt for auto-generated document type templates",
    )
    parser.add_argument("--strategy-latest", default="")
    parser.add_argument("--gate-min-strategy-score", type=float, default=0.70)
    parser.add_argument("--gate-min-regression-pass-rate", type=float, default=0.67)
    parser.add_argument("--gate-min-consecutive-wins", type=int, default=2)
    parser.add_argument(
        "--gate-state-file",
        default=str(PROJECT_ROOT / "artifacts" / "model_promotions" / "gate_state.json"),
    )
    parser.add_argument(
        "--promotion-record-file",
        default=str(PROJECT_ROOT / "artifacts" / "model_promotions" / "latest_promotion.json"),
    )
    parser.add_argument(
        "--regression-eval-set",
        default=str(FINETUNE_DIR / "regression_eval_set.json"),
    )
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    uploads_dir = corpus_dir / "uploads"
    edgar_dir = corpus_dir / "edgar"

    if not args.skip_corpus_build:
        cmd = [
            sys.executable,
            "-u",
            str(FINETUNE_DIR / "build_training_corpus.py"),
            "--output-dir",
            str(corpus_dir),
            "--max-upload-files",
            str(args.max_upload_files),
            "--max-filings-per-query",
            str(args.max_filings_per_query),
            "--max-chars-per-doc",
            str(args.max_chars_per_doc),
            "--edgar-queries",
            args.edgar_queries,
        ]
        if args.sec_user_agent:
            cmd.extend(["--sec-user-agent", args.sec_user_agent])
        if args.include_uploads:
            cmd.append("--include-uploads")
        if args.include_edgar:
            cmd.append("--include-edgar")
        run(cmd, cwd=PROJECT_ROOT)

    extra_dirs = []
    if uploads_dir.exists():
        extra_dirs.append(str(uploads_dir))
    if edgar_dir.exists():
        extra_dirs.append(str(edgar_dir))

    prepare_cmd = [sys.executable, "-u", str(FINETUNE_DIR / "prepare_data.py")]
    for p in extra_dirs:
        prepare_cmd.extend(["--extra-dir", p])
    run(prepare_cmd, cwd=PROJECT_ROOT)

    train_cmd = [sys.executable, "-u", str(FINETUNE_DIR / "train.py")]
    if args.fallback:
        train_cmd.append("--fallback")
    run(train_cmd, cwd=PROJECT_ROOT)

    promoted = False
    if not args.skip_export:
        promotions_dir = Path(args.gate_state_file).parent
        promotions_dir.mkdir(parents=True, exist_ok=True)
        gate_state_path = Path(args.gate_state_file)
        promotion_record_path = Path(args.promotion_record_file)
        gate_state = _safe_read_json(gate_state_path)
        previous_promoted_model = str(gate_state.get("last_promoted_model", OLLAMA_MODEL_NAME))
        consecutive_wins = int(gate_state.get("consecutive_wins", 0))

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_tag = OLLAMA_MODEL_NAME.replace(":", "-")
        candidate_model_name = f"{base_tag}-candidate-{timestamp}:latest"

        run(
            [
                sys.executable,
                "-u",
                str(FINETUNE_DIR / "export_to_ollama.py"),
                "--model-name",
                candidate_model_name,
            ],
            cwd=PROJECT_ROOT,
        )

        eval_out_path = promotions_dir / f"eval_{timestamp}.json"
        run(
            [
                sys.executable,
                "-u",
                str(FINETUNE_DIR / "evaluate_ollama_model.py"),
                "--model-name",
                candidate_model_name,
                "--eval-set",
                args.regression_eval_set,
                "--output-file",
                str(eval_out_path),
            ],
            cwd=PROJECT_ROOT,
        )
        eval_summary = _safe_read_json(eval_out_path)
        regression_pass_rate = float(eval_summary.get("pass_rate", 0.0))

        strategy_ok = True
        strategy_score = None
        if args.strategy_latest:
            latest = _safe_read_json(Path(args.strategy_latest))
            if latest:
                strategy_score = float(latest.get("best_score", 0.0))
                strategy_ok = strategy_score >= float(args.gate_min_strategy_score)

        regression_ok = regression_pass_rate >= float(args.gate_min_regression_pass_rate)
        qualified = strategy_ok and regression_ok
        consecutive_wins = (consecutive_wins + 1) if qualified else 0
        promote_now = qualified and consecutive_wins >= int(args.gate_min_consecutive_wins)

        if promote_now:
            run(["ollama", "cp", candidate_model_name, OLLAMA_MODEL_NAME], cwd=PROJECT_ROOT)
            promoted = True
            gate_state.update(
                {
                    "last_promoted_model": OLLAMA_MODEL_NAME,
                    "last_candidate_model": candidate_model_name,
                    "consecutive_wins": consecutive_wins,
                    "last_result": "promoted",
                    "last_regression_pass_rate": regression_pass_rate,
                    "last_strategy_score": strategy_score,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            promotion_record_path.write_text(
                json.dumps(
                    {
                        "promoted": True,
                        "candidate_model": candidate_model_name,
                        "production_model": OLLAMA_MODEL_NAME,
                        "previous_production_model": previous_promoted_model,
                        "regression_pass_rate": regression_pass_rate,
                        "strategy_score": strategy_score,
                        "consecutive_wins": consecutive_wins,
                        "gate_thresholds": {
                            "min_strategy_score": args.gate_min_strategy_score,
                            "min_regression_pass_rate": args.gate_min_regression_pass_rate,
                            "min_consecutive_wins": args.gate_min_consecutive_wins,
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"\n[PROMOTION] Promoted {candidate_model_name} -> {OLLAMA_MODEL_NAME}")
        else:
            # Automatic rollback behavior: keep current promoted model unchanged.
            try:
                run(["ollama", "rm", candidate_model_name], cwd=PROJECT_ROOT)
            except Exception:
                pass
            gate_state.update(
                {
                    "last_promoted_model": previous_promoted_model,
                    "last_candidate_model": candidate_model_name,
                    "consecutive_wins": consecutive_wins,
                    "last_result": "rollback_kept_previous",
                    "last_regression_pass_rate": regression_pass_rate,
                    "last_strategy_score": strategy_score,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            promotion_record_path.write_text(
                json.dumps(
                    {
                        "promoted": False,
                        "candidate_model": candidate_model_name,
                        "kept_model": previous_promoted_model,
                        "regression_pass_rate": regression_pass_rate,
                        "strategy_score": strategy_score,
                        "consecutive_wins": consecutive_wins,
                        "gate_thresholds": {
                            "min_strategy_score": args.gate_min_strategy_score,
                            "min_regression_pass_rate": args.gate_min_regression_pass_rate,
                            "min_consecutive_wins": args.gate_min_consecutive_wins,
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                        "reason": "Did not meet promotion gate or single-win guard.",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(
                "\n[PROMOTION] No promotion. "
                f"Strategy ok={strategy_ok}, regression ok={regression_ok}, consecutive_wins={consecutive_wins}. "
                "Kept current promoted model."
            )

        gate_state_path.write_text(json.dumps(gate_state, indent=2), encoding="utf-8")

    if not args.skip_doc_type_improvement:
        run(
            [
                sys.executable,
                "-u",
                str(FINETUNE_DIR / "improve_document_types.py"),
                "--corpus-dir",
                str(corpus_dir),
                "--guidance",
                args.doc_type_guidance,
            ],
            cwd=PROJECT_ROOT,
        )

    if promoted:
        print("\nPipeline complete. Promotion applied.")
    else:
        print("\nPipeline complete. Promotion gate kept previous model.")


if __name__ == "__main__":
    main()
