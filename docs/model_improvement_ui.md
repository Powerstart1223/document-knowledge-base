## Model Improvement UI

A built-in admin UI now exists in the Streamlit app for background model improvement jobs.

Where to open it:
- Top navigation: `Model Improvement`
- Sidebar (admin): `Model Improvement`

What you can do:
- Enter an original prompt for model improvement.
- Generate EDGAR keywords/queries from that prompt using OpenAI.
- Run local strategy + local weight training directly from the prompt + generated EDGAR queries.
- Start/stop `Strategy Agents` job (prompt/sampling optimization).
  - Multiple strategy jobs can run in parallel.
  - Each job gets its own progress, ETA, and execution log panel.
- Start/stop `True Weight Training` job (LoRA fine-tuning + Ollama export).
  - Multiple weight-training jobs can run in parallel with per-job logs.
- Set preferences directly in the UI:
  - original prompt / base system prompt
  - generate EDGAR queries from that prompt using OpenAI (editable after generation)
  - additional EDGAR queries appended by the user
  - document-type guidance prompt
  - include uploads / include EDGAR / fallback training mode
- Monitor live status (running/stopped + PID), per-job strategy progress %, stage, ETA, best score, and per-job tail logs.

Background behavior:
- Jobs run as detached subprocesses from the app process.
- PID/meta/log files are stored under `artifacts/ui_jobs/`.
- Strategy progress snapshots are stored at `artifacts/agent_improvement/progress.json`.
- Stop uses `taskkill` to terminate the running pipeline.
