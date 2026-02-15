# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Corporate Law Document Generator — a Python RAG (Retrieval-Augmented Generation) web application built with Streamlit. Multi-user system with authentication where users can upload legal documents, generate AI-powered legal drafts, and chat with their documents using RAG. Features per-user data isolation, role-based access control, modern professional UI, and first-run onboarding. Supports both OpenAI (cloud) and Ollama (local) LLM backends.

### Key Features
- **Multi-user authentication** with bcrypt password hashing, login/registration, session management
- **First-run onboarding wizard** that guides users through API key setup on first login
- **Per-user data isolation** via separate ChromaDB collections per user
- **Role-based access** with admin and user roles, admin panel for user management
- **Modern, user-friendly UX** with professional corporate theme, helpful empty states, clear error messages
- **Enhanced security** with password validation, session management, per-user namespaced data

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
`streamlit_app.py` — authenticated multi-user Streamlit app with modern two-path workflow:
- **Authentication**: Login/registration pages with secure bcrypt password hashing, session management
- **Landing Page**: Two main workflow cards presented after login:
  - **Path A — Edit Existing Document**: Upload → Preview → AI-assisted editing via chat → Download
  - **Path B — Create New Document**: Document type selection → AI-generated dynamic field discovery → Form filling → Generation → AI-assisted editing via chat → Download
- **Settings** (accessed via sidebar gear icon): LLM provider config, user profile management, admin panel (admin users only)
- **Sidebar**: User info badge, logout button, settings access, connection status indicators

### Core modules
- `llm_backend.py` — `LLMBackend` class. Uses `openai>=1.0` client pointed at Ollama's OpenAI-compatible endpoint (`http://localhost:11434/v1`). Supports Ollama and OpenAI with the same interface. Passes `num_ctx=8192` via `extra_body` for Ollama to extend the default 2048-token context.
- `document_generator.py` — `DocumentGenerator` class + `DOCUMENT_TYPES` dict. Handles: style example retrieval from ChromaDB (filtered by `document_type` metadata), optional SEC EDGAR / NetDocuments reference data fetch, prompt construction (system + user), LLM generation, and `.docx` output via `python-docx`.
- `api_clients.py` — External data source clients:
  - `SECEdgarClient`: Free public SEC EDGAR full-text search and company filings API.
  - `NetDocumentsClient`: OAuth 2.0 wrapper around NetDocuments REST API (wraps existing `netdocuments_direct_api.py` logic).
  - `LegalDatabaseClient`: Stub for Westlaw / LexisNexis (requires commercial API subscription).

### Authentication & UI modules (NEW in v2.0)
- `auth.py` — `AuthManager` class for user authentication:
  - SQLite user database with bcrypt password hashing
  - User registration with email/password validation
  - Login with session management
  - Admin functions: user activation, role changes, password updates
  - `get_user_collection_name(user_id)` helper for per-user ChromaDB collections
- `auth_ui.py` — Authentication UI components:
  - `render_login_page()`: Login form with default admin credentials notice
  - `render_registration_page()`: User registration with password strength validation
  - `render_admin_panel()`: Admin user management interface (view users, toggle active status, change roles)
  - `render_profile_settings()`: User profile and password change
  - `render_auth_sidebar()`: User info badge and logout button in sidebar
- `styles.py` — Modern UI styling and theme:
  - `get_custom_css()`: Professional corporate theme (navy + gold), card layouts, modern typography
  - `render_header()`: App header with branding and user badge
  - `render_footer()`: App footer with version and disclaimer
  - Helper functions for status badges, connection indicators, cards

### Legacy NetDocuments scripts (standalone, not imported by the app)
- `netdocuments_direct_api.py` — Full OAuth 2.0 client. Kept for reference.
- `simple_netdocs_client.py` — Simplified token-based client. Kept for reference.

### Data flow
1. **Authentication**: User logs in (or registers) → session created with `current_user` in session state
2. **Landing Page**: User selects workflow (Edit Existing or Create New)
3. **Path A — Edit Existing**:
   - Upload document → text extraction → editable preview
   - User chats with AI to request changes → LLM applies changes → updated preview
   - Version history tracks all changes → undo support
   - Download edited document as .docx
4. **Path B — Create New**:
   - Select document type from grid → LLM generates required fields dynamically
   - User fills form → LLM generates complete document
   - Editable preview with AI chat for revisions → download as .docx
5. **Settings**: Accessible via sidebar, configure LLM provider (Ollama/OpenAI), manage profile, admin panel (admin-only)

### Storage
- `users.db` — SQLite database with user accounts (email, password_hash, role, etc.) — **gitignored**
- `chroma_db/` — ChromaDB persistent vector database with per-user collections — **gitignored**
- `uploads/` — user-uploaded files (gitignored, not used in v2.0 — files processed directly to vectors)

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
