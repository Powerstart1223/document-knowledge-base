## Model Improvement UI

A built-in admin UI now exists in the Streamlit app for background model improvement jobs.

Where to open it:
- Top navigation: `Model Improvement`
- Sidebar (admin): `Model Improvement`

What you can do:
- Start/stop `Strategy Agents` job (prompt/sampling optimization).
- Start/stop `True Weight Training` job (LoRA fine-tuning + Ollama export).
- Set preferences directly in the UI:
  - EDGAR queries
  - learning objective/system prompt
  - document-type guidance prompt
  - include uploads / include EDGAR / fallback training mode
- Monitor live status (running/stopped + PID) and tail logs.

Background behavior:
- Jobs run as detached subprocesses from the app process.
- PID/meta/log files are stored under `artifacts/ui_jobs/`.
- Stop uses `taskkill` to terminate the running pipeline.
