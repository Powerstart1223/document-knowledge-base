# Multi-Agent Improvement Loop (EDGAR + Uploads)

This module runs multiple agents in parallel to improve your active model configuration against factual legal tasks built from:

- SEC EDGAR filings
- Your uploaded files in `uploads/`

## What it does

- `UploadIngestionAgent`: reads and extracts text from local uploaded files.
- `EdgarIngestionAgent`: pulls SEC filings using your `SEC_EDGAR_USER_AGENT`.
- `CaseBuilderAgent`: generates benchmark Q/A cases from the ingested corpus.
- `DiscussionAgent`: proposes improved prompt + sampling candidates.
- `EvaluatorAgent` (parallel): runs candidates over all benchmark cases.
- `JudgeAgent`: scores factual alignment and requirement coverage.
- `ImprovementOrchestrator`: keeps best candidate across iterations and writes artifacts.

## Run

From repo root:

```powershell
python -m agents.multi_agent_improver --mode hybrid --iterations 6 --candidates-per-iteration 8 --candidate-workers 6 --case-workers 10 --max-cases 120
```

### EDGAR notes

Set this first (required by SEC):

```powershell
$env:SEC_EDGAR_USER_AGENT="Your Name your@email.com"
```

### Output

Artifacts are written to:

- `artifacts/agent_improvement/latest.json`
- `artifacts/agent_improvement/<timestamp>/iteration_*.json`

`latest.json` includes the best candidate system prompt and sampling settings (`temperature`, `top_p`, `top_k`).

## Suggested continuous run

Use Windows Task Scheduler to run every hour with your chosen command. Keep one output folder and monitor `latest.json` for drift.
