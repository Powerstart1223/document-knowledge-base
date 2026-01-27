# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Corporate Law Document Generator — a Python RAG (Retrieval-Augmented Generation) web application built with Streamlit. Users upload legal documents tagged by type (contract, memo, brief, filing), then generate new documents using a local Llama model via Ollama. Also supports Chat Q&A over uploaded documents. Optional integrations with SEC EDGAR, NetDocuments, and Westlaw/LexisNexis (stub).

## Commands

### Run locally (Windows)
```
run.bat
```
Creates a venv, checks Ollama availability, installs deps, and launches the app.

### Run directly
```
pip install -r requirements.txt
streamlit run streamlit_app.py
```
App runs at http://localhost:8501.

### Prerequisites
- Python 3.10+
- Ollama installed and running (`ollama pull llama3.1:8b`)
- Verify: `http://localhost:11434/api/tags` responds

### Docker
```
docker compose up --build
```

## Architecture

### Entry point
`streamlit_app.py` — three-tab Streamlit app:
- **Tab 1 — Chat Q&A**: RAG over uploaded documents using ChromaDB vector search + LLM.
- **Tab 2 — Generate Document**: Select type (contract/memo/brief/filing), fill form, optionally pull SEC EDGAR / NetDocuments data, generate via LLM, preview, download as .docx.
- **Tab 3 — Settings**: LLM provider (Ollama/OpenAI), model selector, SEC EDGAR config, NetDocuments OAuth flow, Westlaw/Lexis API key.
- **Sidebar**: File upload with document-type tag selector, process button, database stats by type, connection status indicators.

### Core modules
- `llm_backend.py` — `LLMBackend` class. Uses `openai>=1.0` client pointed at Ollama's OpenAI-compatible endpoint (`http://localhost:11434/v1`). Supports Ollama and OpenAI with the same interface. Passes `num_ctx=8192` via `extra_body` for Ollama to extend the default 2048-token context.
- `document_generator.py` — `DocumentGenerator` class + `DOCUMENT_TYPES` dict. Handles: style example retrieval from ChromaDB (filtered by `document_type` metadata), optional SEC EDGAR / NetDocuments reference data fetch, prompt construction (system + user), LLM generation, and `.docx` output via `python-docx`.
- `api_clients.py` — External data source clients:
  - `SECEdgarClient`: Free public SEC EDGAR full-text search and company filings API.
  - `NetDocumentsClient`: OAuth 2.0 wrapper around NetDocuments REST API (wraps existing `netdocuments_direct_api.py` logic).
  - `LegalDatabaseClient`: Stub for Westlaw / LexisNexis (requires commercial API subscription).

### Legacy NetDocuments scripts (standalone, not imported by the app)
- `netdocuments_direct_api.py` — Full OAuth 2.0 client. Kept for reference.
- `simple_netdocs_client.py` — Simplified token-based client. Kept for reference.

### Data flow
1. User uploads documents via sidebar, selects a document type tag (contract/memo/brief/filing/reference).
2. Text extracted (PDF, DOCX, TXT) → chunked → stored in ChromaDB with `document_type` metadata.
3. **Chat Q&A**: query → top-5 chunks from ChromaDB → context + question → LLM → answer with sources.
4. **Document generation**: select type → fill form → retrieve style examples (ChromaDB, filtered by type) → optionally fetch SEC EDGAR / NetDocuments reference data → build prompt → LLM generates document → preview + download as .docx.

### Storage
- `chroma_db/` — ChromaDB persistent vector database (gitignored)
- `uploads/` — user-uploaded files (gitignored)

## Environment Variables

Configured via `.env` (local) or Streamlit Cloud secrets. See `.env.example` for the full list. Key variables:
- `LLM_PROVIDER` — `ollama` (default) or `openai`
- `OLLAMA_MODEL` — model name (default `llama3.1:8b`)
- `OLLAMA_BASE_URL` — Ollama OpenAI-compatible endpoint (default `http://localhost:11434/v1`)
- `OPENAI_API_KEY` — only needed if `LLM_PROVIDER=openai`
- `SEC_EDGAR_USER_AGENT` — name + email for SEC EDGAR API
- `NETDOCUMENTS_CLIENT_ID`, `NETDOCUMENTS_CLIENT_SECRET` — for NetDocuments OAuth
- `LEGAL_DB_API_KEY` — for Westlaw/LexisNexis (stub)

## Key Caveats

- Llama 3.1 8B produces usable drafts but less sophisticated legal language than GPT-4 or 70B models. Generated documents should be reviewed by a human.
- This tool generates drafts. It does not provide legal advice.
- Ollama context window is set to 8192 tokens via `num_ctx`. For very long documents with many style examples, this may still be limiting.
- Westlaw/LexisNexis are stubs — require commercial API subscriptions.
- The app uses `openai>=1.0.0` with the `OpenAI()` client class (not the legacy `openai.ChatCompletion.create` API).
- No test framework or linting is configured.
