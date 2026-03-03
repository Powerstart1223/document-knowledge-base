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
import shlex
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FINETUNE_DIR = PROJECT_ROOT / "finetune"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"\n[RUN] {' '.join(shlex.quote(x) for x in cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd or PROJECT_ROOT), text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")


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

    if not args.skip_export:
        run([sys.executable, "-u", str(FINETUNE_DIR / "export_to_ollama.py")], cwd=PROJECT_ROOT)

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

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
