## Model Improvement UI

A built-in admin UI now exists in the Streamlit app for background model improvement jobs.

Where to open it:
- Top navigation: `Model Improvement`
- Sidebar (admin): `Model Improvement`

What you can do:
- Start/stop `Strategy Agents` job (prompt/sampling optimization).
- Start/stop `True Weight Training` job (LoRA fine-tuning + Ollama export).
- Set preferences directly in the UI:
  - learning objective / base system prompt
  - generate EDGAR queries from that prompt using the local model (editable after generation)
  - additional EDGAR queries appended by the user
  - learning objective/system prompt
  - document-type guidance prompt
  - include uploads / include EDGAR / fallback training mode
- Monitor live status (running/stopped + PID), strategy progress %, stage, ETA, best score, and tail logs.

Background behavior:
- Jobs run as detached subprocesses from the app process.
- PID/meta/log files are stored under `artifacts/ui_jobs/`.
- Strategy progress snapshots are stored at `artifacts/agent_improvement/progress.json`.
- Stop uses `taskkill` to terminate the running pipeline.
