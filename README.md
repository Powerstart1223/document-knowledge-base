# Corporate Law Document Generator v2.0

A RAG-powered legal document generation system with AI-assisted drafting, built for corporate law firms and legal departments.

## âœ¨ What's New in v2.0

### ðŸ” Multi-User Authentication
- **User Registration & Login** - Secure authentication with bcrypt password hashing
- **Role-Based Access** - Admin and user roles with different permissions
- **Per-User Data Isolation** - Each user has their own document collection and chat history
- **Admin Panel** - Manage users, activate/deactivate accounts, and assign roles
- **Session Management** - Secure, persistent sessions with logout functionality

### ðŸŽ¨ Modern UX Overhaul
- **Professional Theme** - Clean, corporate design with navy and gold color scheme
- **Card-Based Layouts** - Modern, organized interface with smooth transitions
- **Improved Chat UI** - Beautiful chat bubbles with better message styling
- **Status Indicators** - Real-time connection status and loading states
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **Enhanced Forms** - Better input styling with validation feedback
- **Toast Notifications** - User-friendly success/error messages

## Features

- **Document Upload & Processing** - Support for PDF, DOCX, and TXT files
- **Smart Chat Q&A** - Ask questions about your documents with RAG-powered answers
- **AI Document Generation** - Generate contracts, legal memos, briefs, and corporate filings
- **Style Learning** - Automatically learns from your existing documents to match your firm's writing style
- **External Data Integration**:
  - SEC EDGAR filings (free, public)
  - Westlaw / LexisNexis support (stub)
- **Cloud & Local Deployment** - Works with OpenAI (cloud) or Ollama (local)
- **Professional Output** - Export to formatted .docx with proper legal document structure

## Quick Start â€” Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Open your browser and login:**
   - Navigate to `http://localhost:8501`
   - On first run, a bootstrap admin is created at `admin@cypressllp.com`
   - Password comes from `BOOTSTRAP_ADMIN_PASSWORD` or is generated and written to `bootstrap_admin_credentials.txt`
   - Change the password immediately after first login

5. **Create additional users:**
   - Click "Create Account" on login screen
   - Registration domain policy is controlled by `ALLOWED_EMAIL_DOMAINS` (`*` allows any domain)
   - Or use Admin panel to manage users

## Quick Start â€” Streamlit Cloud Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

**TL;DR:**
1. Push code to GitHub
2. Deploy to [share.streamlit.io](https://share.streamlit.io)
3. Add your OpenAI API key in Streamlit Cloud Secrets
4. Your app is live!

## Document Generation

Generate professional legal documents using AI:

### Supported Document Types

1. **Contracts / Agreements**
   - Bilateral contracts between parties
   - Includes standard boilerplate clauses
   - Customizable terms and conditions

2. **Legal Memoranda**
   - Internal legal analysis
   - Standard memo format with Q&A structure
   - Jurisdiction-specific research

3. **Legal Briefs / Motions**
   - Court filings with proper citation format
   - Argument structure and legal standards
   - Case caption and procedural requirements

4. **Corporate Filings**
   - Articles of incorporation
   - Annual reports
   - Certificate amendments
   - Optional SEC EDGAR integration for reference data

### How to Generate Documents

1. **Upload Style Examples** (optional but recommended):
   - Upload sample documents of each type in the sidebar
   - Tag them with the correct document type
   - The AI will learn your firm's writing style

2. **Generate a Document**:
   - Go to "Generate Document" tab
   - Select document type
   - Fill in the parameters (parties, dates, terms, etc.)
   - Optionally enable SEC EDGAR for reference data
   - Click "Generate Document"

3. **Review and Download**:
   - Preview the generated draft
   - Download as .docx with proper formatting
   - All documents include disclaimer: "DRAFT â€” FOR ATTORNEY REVIEW ONLY"

## External Integrations

### SEC EDGAR (Free)
- Full-text search of public filings
- Company filing history by CIK
- Automatic integration with corporate filings
- No API key required (just provide User-Agent)

### Westlaw / LexisNexis (Stub)
- API structure ready
- Requires commercial API subscription
- Contact Westlaw/Lexis for API access

## Project Structure

```
document-knowledge-base/
â”œâ”€â”€ streamlit_app.py          # Main Streamlit application
â”œâ”€â”€ llm_backend.py            # LLM abstraction (Ollama/OpenAI)
â”œâ”€â”€ document_generator.py     # Document generation pipeline
â”œâ”€â”€ api_clients.py            # External API clients (SEC EDGAR, etc.)
â”œâ”€â”€ requirements.txt          # Python dependencies
â”œâ”€â”€ .env.example              # Environment variables template
â”œâ”€â”€ .streamlit/
â”‚   â”œâ”€â”€ config.toml           # Streamlit configuration
â”‚   â””â”€â”€ secrets.toml.example  # Secrets template (for Streamlit Cloud)
â”œâ”€â”€ chroma_db/                # ChromaDB vector storage (created at runtime)
â”œâ”€â”€ uploads/                  # Uploaded documents (created at runtime)
â””â”€â”€ DEPLOYMENT.md             # Deployment guide
```

## How it Works

1. **Document Processing**: Documents are chunked and embedded using sentence-transformers
2. **Vector Storage**: ChromaDB stores embeddings with metadata (document type, source)
3. **RAG Chat**: User questions retrieve relevant chunks, then LLM generates answers with citations
4. **Document Generation**:
   - Retrieves style examples from uploaded documents
   - Optionally fetches reference data from SEC EDGAR
   - Builds structured prompts with user parameters
   - Generates professional legal documents via LLM
   - Exports to formatted .docx with proper styling
