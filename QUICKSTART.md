# Quick Start Guide - Corporate Law Document Generator v2.0

Get up and running in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- OpenAI API key (get one at https://platform.openai.com/api-keys)
  - OR Ollama installed locally (https://ollama.ai)

## Installation

### Step 1: Clone or Download

```bash
# If using Git
git clone <your-repo-url>
cd document-knowledge-base

# Or download and extract the ZIP file
```

### Step 2: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure LLM Backend

**Option A: Use OpenAI (works everywhere)**

Create a `.env` file:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
```

**Option B: Use Ollama (local, free)**

1. Install Ollama from https://ollama.ai
2. Pull a model:
   ```bash
   ollama pull llama3.1:8b
   ```
3. Create a `.env` file (optional - auto-detected):
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.1:8b
   ```

## Run the Application

```bash
streamlit run streamlit_app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## First Login

The application creates a default administrator account on first run:

- **Email:** `admin@lawfirm.com`
- **Password:** `Admin123!`

**🔐 IMPORTANT:** Change this password immediately after first login!

1. Login with the default credentials
2. Go to **Settings** → **Profile**
3. Click "Change Password"
4. Enter current password and new strong password

## Create Your First Document

### 1. Upload Sample Documents (Optional but Recommended)

This trains the AI to match your writing style:

1. In the sidebar, select a document type (e.g., "Contract / Agreement")
2. Click "Browse files" and upload a sample contract (PDF, DOCX, or TXT)
3. Click "Process Documents"
4. Repeat for other document types (memos, briefs, filings)

### 2. Generate a Document

1. Go to the **Generate Document** tab
2. Select document type (e.g., "Contract / Agreement")
3. Fill in the parameters:
   - Party A: `Acme Corporation`
   - Party B: `Beta LLC`
   - Effective Date: `2026-01-01`
   - Subject Matter: `Software licensing agreement`
   - Key Terms: `Annual subscription, source code escrow, unlimited users`
4. Click "Generate Document"
5. Preview the generated draft
6. Click "Download as .docx"

### 3. Chat with Your Documents

1. Go to the **Chat Q&A** tab
2. Type a question like: "What are the key terms of the Acme-Beta agreement?"
3. The AI will search your uploaded documents and provide an answer with source citations

## Add More Users

### For Team Members

1. Click "Create Account" on the login page
2. Fill in email, name, and password
3. Click "Create Account"
4. New users start with "user" role

### For Administrators

1. Login as admin
2. Go to **Settings** → **Admin** tab
3. View all registered users
4. Click "→ Admin" to promote a user to administrator
5. Click "Activate/Deactivate" to enable/disable accounts

## Key Features

### Per-User Data Isolation
- Each user has their own document collection
- Users cannot see other users' documents
- Chat history is private per user

### Role-Based Access
- **Admin:** Can manage users, access admin panel
- **User:** Can upload documents, chat, generate documents

### Document Types
1. **Contract / Agreement** - Bilateral contracts with standard clauses
2. **Legal Memorandum** - Internal legal analysis with Q&A format
3. **Legal Brief** - Court filings with citations
4. **Corporate Filing** - Articles of incorporation, annual reports, etc.

## Configuration (Optional)

### SEC EDGAR Integration (Free)

Add to your `.env`:
```bash
SEC_EDGAR_USER_AGENT=YourName your@email.com
```

Or configure in **Settings** → **Integrations** → **SEC EDGAR**

## Troubleshooting

### "LLM is not available"

**With OpenAI:**
- Check your API key is correct in `.env`
- Verify key starts with `sk-`
- Check you have credits in your OpenAI account

**With Ollama:**
- Make sure Ollama is running: `ollama list`
- Check model is pulled: `ollama pull llama3.1:8b`
- Verify Ollama is running at http://localhost:11434

### "Module not found" errors

```bash
# Make sure virtual environment is activated
# Then reinstall dependencies:
pip install --upgrade -r requirements.txt
```

### "Cannot login with default credentials"

The `users.db` file may be corrupted:
```bash
# Delete the database (will reset all users)
rm users.db  # macOS/Linux
del users.db  # Windows

# Restart the app - default admin will be recreated
streamlit run streamlit_app.py
```

### Slow first load

ChromaDB downloads embedding models on first run (2-3 minutes). This only happens once and subsequent loads are fast.

## Next Steps

1. **Customize Settings**
   - Configure your preferred LLM model
   - Set up external integrations (SEC EDGAR)

2. **Upload Style Examples**
   - Upload your firm's existing documents
   - Tag them by type
   - The AI will learn your writing style

3. **Create Team Accounts**
   - Register accounts for your team members
   - Use admin panel to manage access

4. **Deploy to Cloud**
   - See [DEPLOYMENT.md](DEPLOYMENT.md) for Streamlit Cloud deployment
   - Share with your team via public URL

## Security Notes

- All passwords are hashed with bcrypt (never stored in plaintext)
- Sessions are secure and isolated
- Each user's documents are private
- Admin panel allows account management
- Default admin password **must** be changed

## Getting Help

- Check [README.md](README.md) for feature overview
- See [DEPLOYMENT.md](DEPLOYMENT.md) for cloud deployment
- Review [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) if upgrading from v1.0
- Check application logs in terminal for detailed errors

## Enjoy!

You're all set! Start generating professional legal documents with AI assistance.

**Remember:** All generated documents are drafts and must be reviewed by a qualified attorney before use.
