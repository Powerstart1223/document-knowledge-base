# Streamlit Cloud Deployment Checklist

Use this checklist to ensure your app is ready for Streamlit Cloud deployment.

## Pre-Deployment Checklist

### Code Readiness
- [x] Main file is named `streamlit_app.py` (Streamlit Cloud default)
- [x] All dependencies are in `requirements.txt` with version constraints
- [x] No hard-coded secrets in source code
- [x] `.env` and `.streamlit/secrets.toml` are in `.gitignore`
- [x] App gracefully handles missing environment variables
- [x] LLM provider auto-detects cloud environment
- [x] Proper error messages when API keys are missing

### Secrets Management
- [x] `.streamlit/secrets.toml.example` exists with documentation
- [x] All secrets use Streamlit secrets or environment variables
- [x] No API keys committed to git
- [ ] **ACTION REQUIRED:** You must configure secrets in Streamlit Cloud dashboard

### Dependencies
- [x] `requirements.txt` has all packages with version pins
- [x] No local-only dependencies (e.g., Ollama is optional, not required)
- [x] ChromaDB and sentence-transformers are compatible with Streamlit Cloud

### Functionality
- [x] App defaults to OpenAI provider on cloud environment
- [x] Helpful error messages when LLM is not configured
- [x] Settings tab shows environment detection
- [x] All features work without local dependencies

## Deployment Steps

### 1. Push to GitHub

```bash
# Verify secrets are not tracked
git status

# If .streamlit/secrets.toml or .env appear, add them to .gitignore
# These files should NEVER be committed

# Commit all changes
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 2. Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `YOUR_USERNAME/document-knowledge-base`
5. Set branch: `main`
6. Set main file: `streamlit_app.py`
7. Click "Deploy"

### 3. Configure Secrets

In Streamlit Cloud dashboard → Your App → Settings → Secrets, paste:

```toml
# Required: OpenAI Configuration
LLM_PROVIDER = "openai"
OPENAI_API_KEY = "sk-proj-YOUR_ACTUAL_KEY_HERE"
OPENAI_MODEL = "gpt-4o-mini"

# Optional: SEC EDGAR
SEC_EDGAR_USER_AGENT = "YourName your@email.com"

# Optional: Legal Databases
LEGAL_DB_API_KEY = ""
```

**Important:**
- Replace `sk-proj-YOUR_ACTUAL_KEY_HERE` with your real OpenAI API key
- Get API key from https://platform.openai.com/api-keys
- `gpt-4o-mini` is recommended for cost-effectiveness

### 4. Verify Deployment

After secrets are saved, test:

1. **Home Page Loads**
   - App should load without errors
   - LLM status should show "OpenAI (gpt-4o-mini)" in sidebar

2. **Document Upload**
   - Upload a test PDF or DOCX
   - Click "Process Documents"
   - Should see "Processed X files into Y chunks"

3. **Chat Q&A**
   - Ask a question about the uploaded document
   - Should receive AI-generated answer with source citation

4. **Document Generation**
   - Go to "Generate Document" tab
   - Select a document type (e.g., "Legal Memorandum")
   - Fill in required fields
   - Click "Generate Document"
   - Should generate a draft document
   - Click "Download as .docx" to verify export

5. **Settings**
   - Verify "Running on Streamlit Cloud" message appears
   - LLM provider should be "OpenAI"
   - API key validation should show "API key format looks valid"

## Troubleshooting

### "LLM is not available" Error

**Symptoms:** Red error banner on home page

**Solutions:**
1. Check Streamlit Cloud Secrets dashboard
2. Verify `OPENAI_API_KEY` is set correctly
3. Ensure key starts with `sk-`
4. Verify key is valid at https://platform.openai.com/api-keys
5. Check `LLM_PROVIDER = "openai"` (not "ollama")

### Import Errors

**Symptoms:** App fails to start with "ModuleNotFoundError"

**Solutions:**
1. Check build logs in Streamlit Cloud dashboard
2. Verify package is in `requirements.txt`
3. Try pinning specific version in `requirements.txt`

### ChromaDB / Sentence-Transformers Slow

**Symptoms:** App takes 2-3 minutes to start on first load

**Solution:**
- This is normal behavior
- ChromaDB downloads embedding models on first run
- Subsequent loads are fast (models are cached)

### Documents Not Persisting

**Symptoms:** Uploaded documents disappear after app restart

**Explanation:**
- ChromaDB data is ephemeral on Streamlit Cloud free tier
- Data persists during a session but resets on redeploy
- This is expected behavior for free tier
- For persistent storage, consider:
  - Streamlit Cloud paid tier with persistent storage
  - External vector database (Pinecone, Weaviate, etc.)
  - Cloud storage for ChromaDB directory

## Cost Estimates

### Streamlit Cloud
- **Free tier:** Unlimited public apps
- **Private apps:** $20/month per app

### OpenAI API Costs
- **gpt-4o-mini:** $0.150 per 1M input tokens, $0.600 per 1M output tokens
- **gpt-4o:** $2.50 per 1M input tokens, $10.00 per 1M output tokens
- **Estimated monthly cost for moderate use:** $5-20

**Cost optimization tips:**
- Use `gpt-4o-mini` for most operations (10x cheaper than gpt-4)
- Limit max_tokens in generation (currently 4096)
- Monitor usage at https://platform.openai.com/usage

## Security Best Practices

- [ ] Never commit `.env` or `.streamlit/secrets.toml`
- [ ] Use strong, unique API keys
- [ ] Rotate API keys periodically
- [ ] Monitor OpenAI usage dashboard for anomalies
- [ ] Use private Streamlit Cloud apps for sensitive data
- [ ] Review all generated documents before using in production

## Post-Deployment

### Share Your App
Your app is live at: `https://YOUR_APP_NAME.streamlit.app`

### Custom Domain (Paid Tier)
Streamlit Cloud supports custom domains on paid plans.

### Monitoring
- Check Streamlit Cloud dashboard for:
  - App uptime
  - Error logs
  - Resource usage
- Check OpenAI dashboard for:
  - API usage
  - Cost tracking
  - Rate limit usage

### Updates
When you push to GitHub, Streamlit Cloud auto-deploys:
```bash
git add .
git commit -m "Update feature X"
git push origin main
# Streamlit Cloud will automatically rebuild and deploy
```

## Need Help?

- **Streamlit Cloud Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **OpenAI Platform:** https://platform.openai.com/docs
- **This Project's Issues:** GitHub Issues tab

---

**Ready to deploy?** Follow the steps above and you'll have your app live in 5 minutes!
