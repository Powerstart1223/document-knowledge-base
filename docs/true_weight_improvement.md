# True Weight Improvement + Document-Type Growth

This pipeline performs real model weight updates (LoRA fine-tuning) and updates your generated document type catalog.

## What runs

1. `finetune/build_training_corpus.py`
   - Pulls corpus from:
     - `uploads/`
     - SEC EDGAR filings
   - Writes normalized `.txt` files to `finetune_output/corpus/`.

2. `finetune/prepare_data.py`
   - Builds ShareGPT training JSONL from your base folders + corpus folders.

3. `finetune/train.py`
   - Runs QLoRA fine-tuning (actual weight updates in LoRA adapters).

4. `finetune/export_to_ollama.py`
   - Exports/quantizes and registers a candidate model in Ollama.

5. `finetune/evaluate_ollama_model.py`
   - Runs a fixed regression suite from `finetune/regression_eval_set.json`.

6. Promotion gate (inside `continuous_weight_improvement.py`)
   - Requires:
     - minimum strategy score threshold (if provided),
     - minimum regression pass-rate threshold,
     - minimum consecutive wins (default `2`).
   - Prevents single-win promotion.
   - If gate fails, candidate is removed and previous promoted model is kept (automatic rollback behavior).

7. `finetune/improve_document_types.py`
   - Discovers recurring new document types and appends templates to `document_types_generated.json`.

8. `finetune/continuous_weight_improvement.py`
   - Orchestrates all of the above end-to-end.

## One command

```powershell
python finetune/continuous_weight_improvement.py --include-uploads --include-edgar
```

## Background run on Windows

Create logs directory:

```powershell
mkdir C:\Users\SJK\document-knowledge-base\logs -Force
```

Schedule a nightly run:

```powershell
schtasks /Create /SC DAILY /ST 01:30 /TN "DocKB-TrueWeight-Improve" /TR "powershell -NoProfile -WindowStyle Hidden -Command `"cd C:\Users\SJK\document-knowledge-base; $env:SEC_EDGAR_USER_AGENT='Your Name your@email.com'; python finetune/continuous_weight_improvement.py --include-uploads --include-edgar --fallback >> logs\true_weight_improvement.log 2>&1`"" /F
```

Run immediately:

```powershell
schtasks /Run /TN "DocKB-TrueWeight-Improve"
```

Check progress:

```powershell
Get-Content C:\Users\SJK\document-knowledge-base\logs\true_weight_improvement.log -Tail 200
```
