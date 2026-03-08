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
import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
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


def _is_within_window(now: datetime, start_hour: int, end_hour: int) -> bool:
    if start_hour == end_hour:
        return True
    current_hour = now.hour
    if start_hour < end_hour:
        return start_hour <= current_hour < end_hour
    return current_hour >= start_hour or current_hour < end_hour


def _next_window_start(now: datetime, start_hour: int, end_hour: int) -> datetime:
    candidate = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if _is_within_window(now, start_hour, end_hour):
        return now
    if start_hour < end_hour:
        if now.hour < start_hour:
            return candidate
        return candidate + timedelta(days=1)
    if now.hour < start_hour and now.hour >= end_hour:
        return candidate
    return candidate + timedelta(days=1)


def _write_progress(progress_file: Path | None, payload: dict) -> None:
    if not progress_file:
        return
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    progress_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _system_snapshot() -> dict:
    snapshot = {
        "captured_at": datetime.now().isoformat(),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
    }
    try:
        usage = shutil.disk_usage(str(PROJECT_ROOT))
        snapshot["disk_free_gb"] = round(usage.free / 1024**3, 2)
    except Exception:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            snapshot["gpu"] = {
                "name": props.name,
                "total_memory_gb": round(props.total_memory / 1024**3, 2),
            }
    except Exception:
        pass
    return snapshot


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
    parser.add_argument("--scan-drives", action="store_true", help="Discover new documents across accessible drives before training")
    parser.add_argument(
        "--drive-inventory-file",
        default=str(PROJECT_ROOT / "artifacts" / "document_inventory" / "latest_inventory.json"),
    )
    parser.add_argument(
        "--drive-inventory-markdown",
        default=str(PROJECT_ROOT / "artifacts" / "document_inventory" / "latest_inventory.md"),
    )
    parser.add_argument(
        "--drive-corpus-dir",
        default=str(PROJECT_ROOT / "finetune_output" / "corpus" / "discovered_drives"),
    )
    parser.add_argument("--drive-scan-max-files", type=int, default=5000)
    parser.add_argument("--job-key", default="")
    parser.add_argument("--progress-file", default="")
    parser.add_argument("--allowed-start-hour", type=int, default=0)
    parser.add_argument("--allowed-end-hour", type=int, default=6)
    parser.add_argument("--max-start-delay-hours", type=float, default=24.0)
    args = parser.parse_args()

    progress_file = Path(args.progress_file) if args.progress_file else None
    system_snapshot = _system_snapshot()
    progress_state = {
        "job_key": args.job_key,
        "status": "starting",
        "phase": "starting",
        "percent": 0.0,
        "message": "Initializing weight-improvement pipeline.",
        "updated_at": datetime.now().isoformat(),
        "window": {
            "allowed_start_hour": int(args.allowed_start_hour),
            "allowed_end_hour": int(args.allowed_end_hour),
        },
        "system": system_snapshot,
    }

    def update_progress(
        *,
        status: str,
        phase: str,
        percent: float,
        message: str,
        step_index: int | None = None,
        step_total: int | None = None,
        current_command: list[str] | None = None,
        extra: dict | None = None,
    ) -> None:
        progress_state.update(
            {
                "status": status,
                "phase": phase,
                "percent": round(max(0.0, min(100.0, percent)), 1),
                "message": message,
                "updated_at": datetime.now().isoformat(),
            }
        )
        if step_index is not None:
            progress_state["step_index"] = step_index
        if step_total is not None:
            progress_state["step_total"] = step_total
        if current_command is not None:
            progress_state["current_command"] = current_command
        if extra:
            progress_state.update(extra)
        _write_progress(progress_file, progress_state)

    start_hour = int(args.allowed_start_hour) % 24
    end_hour = int(args.allowed_end_hour) % 24
    delay_deadline = datetime.now() + timedelta(hours=max(0.0, float(args.max_start_delay_hours)))

    print("[PIPELINE] Weight improvement pipeline starting")
    print(f"[PIPELINE] Window: {start_hour:02d}:00 to {end_hour:02d}:00 local time")
    print(f"[PIPELINE] System snapshot: {json.dumps(system_snapshot, indent=2)}")

    while True:
        now = datetime.now()
        if _is_within_window(now, start_hour, end_hour):
            break
        next_start = _next_window_start(now, start_hour, end_hour)
        if next_start > delay_deadline:
            message = (
                "Next allowed training window starts after the configured maximum delay. "
                f"Next window: {next_start.isoformat()}"
            )
            update_progress(
                status="failed",
                phase="window_wait",
                percent=0.0,
                message=message,
                extra={"next_allowed_start_at": next_start.isoformat(), "failed_at": datetime.now().isoformat()},
            )
            raise RuntimeError(message)
        remaining_seconds = max(1, int((next_start - now).total_seconds()))
        message = (
            "Waiting for overnight window before starting heavy training work. "
            f"Next allowed start: {next_start.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"[SCHEDULE] {message}")
        update_progress(
            status="pending",
            phase="window_wait",
            percent=0.0,
            message=message,
            extra={
                "next_allowed_start_at": next_start.isoformat(),
                "seconds_until_start": remaining_seconds,
            },
        )
        time.sleep(min(60, remaining_seconds))

    corpus_dir = Path(args.corpus_dir)
    uploads_dir = corpus_dir / "uploads"
    edgar_dir = corpus_dir / "edgar"
    drive_corpus_dir = Path(args.drive_corpus_dir)
    current_step = 0
    total_steps = (
        2
        + (1 if args.scan_drives else 0)
        + (0 if args.skip_corpus_build else 1)
        + (0 if args.skip_export else 3)
        + (0 if args.skip_doc_type_improvement else 1)
    )

    def begin_step(phase: str, message: str, command: list[str] | None = None) -> None:
        nonlocal current_step
        current_step += 1
        percent = ((current_step - 1) / max(total_steps, 1)) * 100.0
        update_progress(
            status="running",
            phase=phase,
            percent=percent,
            message=message,
            step_index=current_step,
            step_total=total_steps,
            current_command=command,
            extra={"started_heavy_work_at": progress_state.get("started_heavy_work_at") or datetime.now().isoformat()},
        )

    def complete_step(phase: str, message: str, extra: dict | None = None) -> None:
        percent = (current_step / max(total_steps, 1)) * 100.0
        update_progress(
            status="running",
            phase=phase,
            percent=percent,
            message=message,
            step_index=current_step,
            step_total=total_steps,
            current_command=progress_state.get("current_command"),
            extra=extra,
        )

    promoted = False
    try:
        if args.scan_drives:
            scan_cmd = [
                sys.executable,
                "-u",
                str(FINETUNE_DIR / "scan_document_landscape.py"),
                "--output-file",
                args.drive_inventory_file,
                "--markdown-file",
                args.drive_inventory_markdown,
                "--corpus-dir",
                str(drive_corpus_dir),
                "--max-total-files",
                str(args.drive_scan_max_files),
            ]
            begin_step(
                "scan_document_landscape",
                "Scanning accessible drives for new legal documents and building the inventory report.",
                scan_cmd,
            )
            run(scan_cmd, cwd=PROJECT_ROOT)
            complete_step(
                "scan_document_landscape",
                "Drive scan and inventory build completed.",
                {
                    "drive_inventory_file": args.drive_inventory_file,
                    "drive_inventory_markdown": args.drive_inventory_markdown,
                    "drive_corpus_dir": str(drive_corpus_dir),
                },
            )

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
            begin_step("build_corpus", "Building training corpus from the selected sources.", cmd)
            run(cmd, cwd=PROJECT_ROOT)
            complete_step("build_corpus", "Training corpus build completed.")

        extra_dirs = []
        if uploads_dir.exists():
            extra_dirs.append(str(uploads_dir))
        if edgar_dir.exists():
            extra_dirs.append(str(edgar_dir))
        if args.scan_drives and drive_corpus_dir.exists():
            extra_dirs.append(str(drive_corpus_dir))

        prepare_cmd = [sys.executable, "-u", str(FINETUNE_DIR / "prepare_data.py")]
        for p in extra_dirs:
            prepare_cmd.extend(["--extra-dir", p])
        begin_step("prepare_data", "Preparing ShareGPT training data.", prepare_cmd)
        run(prepare_cmd, cwd=PROJECT_ROOT)
        complete_step("prepare_data", "Training data preparation completed.")

        train_cmd = [sys.executable, "-u", str(FINETUNE_DIR / "train.py")]
        if args.fallback:
            train_cmd.append("--fallback")
        begin_step(
            "train_lora",
            "Starting LoRA training with conservative settings. This is the heaviest stage.",
            train_cmd,
        )
        run(train_cmd, cwd=PROJECT_ROOT)
        complete_step("train_lora", "LoRA training completed.")

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

            export_cmd = [
                sys.executable,
                "-u",
                str(FINETUNE_DIR / "export_to_ollama.py"),
                "--model-name",
                candidate_model_name,
            ]
            begin_step("export_ollama", f"Exporting candidate model {candidate_model_name} to Ollama.", export_cmd)
            run(export_cmd, cwd=PROJECT_ROOT)
            complete_step("export_ollama", "Candidate model export completed.", {"candidate_model_name": candidate_model_name})

            eval_out_path = promotions_dir / f"eval_{timestamp}.json"
            eval_cmd = [
                sys.executable,
                "-u",
                str(FINETUNE_DIR / "evaluate_ollama_model.py"),
                "--model-name",
                candidate_model_name,
                "--eval-set",
                args.regression_eval_set,
                "--output-file",
                str(eval_out_path),
            ]
            begin_step("evaluate_candidate", "Running regression evaluation against the candidate model.", eval_cmd)
            run(eval_cmd, cwd=PROJECT_ROOT)
            eval_summary = _safe_read_json(eval_out_path)
            regression_pass_rate = float(eval_summary.get("pass_rate", 0.0))
            complete_step(
                "evaluate_candidate",
                f"Candidate evaluation completed with pass rate {regression_pass_rate:.2%}.",
                {"regression_pass_rate": regression_pass_rate, "eval_output_file": str(eval_out_path)},
            )

            begin_step("promotion_gate", "Applying the promotion gate to decide whether to replace the active model.")
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
            complete_step(
                "promotion_gate",
                "Promotion gate completed." if promoted else "Promotion gate kept the previous production model.",
                {
                    "promoted": promoted,
                    "candidate_model_name": candidate_model_name,
                    "gate_state_file": str(gate_state_path),
                    "promotion_record_file": str(promotion_record_path),
                    "strategy_score": strategy_score,
                },
            )

        if not args.skip_doc_type_improvement:
            doc_type_cmd = [
                sys.executable,
                "-u",
                str(FINETUNE_DIR / "improve_document_types.py"),
                "--corpus-dir",
                str(corpus_dir),
                "--guidance",
                args.doc_type_guidance,
            ]
            begin_step("doc_type_growth", "Refreshing generated document types from the latest corpus.", doc_type_cmd)
            run(doc_type_cmd, cwd=PROJECT_ROOT)
            complete_step("doc_type_growth", "Document type improvement completed.")

        final_message = "Pipeline complete. Promotion applied." if promoted else "Pipeline complete. Promotion gate kept previous model."
        print(f"\n{final_message}")
        update_progress(
            status="completed",
            phase="complete",
            percent=100.0,
            message=final_message,
            step_index=total_steps,
            step_total=total_steps,
            current_command=None,
            extra={"completed_at": datetime.now().isoformat(), "promoted": promoted},
        )
    except Exception as exc:
        failure_message = f"Pipeline failed: {exc}"
        print(f"\n[ERROR] {failure_message}")
        update_progress(
            status="failed",
            phase=str(progress_state.get("phase") or "failed"),
            percent=float(progress_state.get("percent") or 0.0),
            message=failure_message,
            step_index=progress_state.get("step_index"),
            step_total=progress_state.get("step_total"),
            current_command=progress_state.get("current_command"),
            extra={"failed_at": datetime.now().isoformat(), "error": str(exc)},
        )
        raise


if __name__ == "__main__":
    main()
