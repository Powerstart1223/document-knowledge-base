# 🌐 Deployment Guide — Corporate Law Document Generator v2.0

This guide covers deploying the Corporate Law Document Generator with the new multi-user authentication system and modern UX to Streamlit Cloud.

## 🚀 Quick Start: Streamlit Cloud (Recommended)

**🆓 Free Tier Available | ⚡ 5-Minute Setup | 🔄 Auto-Deploy from Git**

### Prerequisites

- GitHub account
- OpenAI API key (get one at https://platform.openai.com/api-keys)
- Git repository with your code

### Step 1: Prepare Your Repository

```bash
# Initialize git if not already done
git init

# Add all files (secrets are excluded via .gitignore)
git add .

# Commit your code
git commit -m "Initial commit for Streamlit Cloud deployment"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub account (if not already connected)
4. Select your repository
5. Set the main file path: `streamlit_app.py`
6. Click "Deploy"

### Step 3: Configure Secrets

The app requires an OpenAI API key to function. Configure it in Streamlit Cloud:

1. In your Streamlit Cloud dashboard, open your app
2. Click the "Settings" menu (⋮) → "Secrets"
3. Paste the following configuration (replace with your actual values):

```toml
# Required: LLM Configuration
LLM_PROVIDER = "openai"
OPENAI_API_KEY = "sk-proj-YOUR_ACTUAL_API_KEY_HERE"
OPENAI_MODEL = "gpt-4o-mini"

# Optional: SEC EDGAR (free, just provide your contact info)
SEC_EDGAR_USER_AGENT = "YourName your@email.com"

# Optional: Westlaw/LexisNexis
LEGAL_DB_API_KEY = ""
```

4. Click "Save"
5. Your app will automatically restart with the new secrets

### Step 4: First Login

**⚠️ IMPORTANT: Default Admin Credentials**

On first run, the application automatically creates a default administrator account:
- **Email:** `admin@lawfirm.com`
- **Password:** `Admin123!`

**🔐 Security Note:** Change this password immediately after first login!

1. Navigate to your deployed app: `https://YOUR_APP_NAME.streamlit.app`
2. You'll see the login screen
3. Login with the default admin credentials above
4. Go to Settings → Profile → Change Password
5. Set a strong, unique password

### Step 5: Create Additional Users

As an administrator, you can:
1. Have team members register their own accounts (they'll be created as regular users)
2. In Settings → Admin panel, you can:
   - View all registered users
   - Activate/deactivate accounts
   - Change user roles (promote users to admin)
   - Monitor user activity

### Step 6: Verify Deployment

Test the following features:
   - Upload a document (PDF, DOCX, or TXT) in the sidebar
   - Process the document
   - Ask a question in the "Chat Q&A" tab
   - Generate a document in the "Generate Document" tab
   - Each user sees only their own documents (data isolation)

### Troubleshooting

**"LLM is not available" error:**
- Check that your `OPENAI_API_KEY` is correctly set in Streamlit Cloud Secrets
- Verify the API key is valid at https://platform.openai.com/api-keys
- Make sure `LLM_PROVIDER = "openai"` (not "ollama")

**Import errors:**
- Check that all dependencies are in `requirements.txt`
- Streamlit Cloud will show build logs if packages fail to install

**App is slow on first load:**
- ChromaDB and sentence-transformers download models on first run
- This is normal and only happens once

---

### Option 2: Docker + Any Cloud (Most Flexible)
**🐳 Containerized | 🌍 Deploy Anywhere | 🔧 Full Control**

1. **Build and Test Locally:**
   ```bash
   # Build the image
   docker build -t document-knowledge-base .

   # Test locally
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY=your_key_here \
     document-knowledge-base
   ```

2. **Deploy to Cloud Platforms:**

   **Railway.app:**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login and deploy
   railway login
   railway init
   railway up
   ```

   **Render.com:**
   - Connect GitHub repository
   - Select "Web Service"
   - Use `render.yaml` configuration
   - Add environment variables

   **Google Cloud Run:**
   ```bash
   # Build and push to registry
   gcloud builds submit --tag gcr.io/PROJECT_ID/document-kb

   # Deploy
   gcloud run deploy --image gcr.io/PROJECT_ID/document-kb
   ```

### Option 3: Traditional VPS/Server
**💻 Full Control | 🔒 Private Hosting | 💰 Cost Varies**

1. **Server Setup (Ubuntu/Debian):**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Install Docker Compose
   sudo apt install docker-compose -y
   ```

2. **Deploy with Docker Compose:**
   ```bash
   # Clone your repository
   git clone your-repo-url
   cd document-knowledge-base

   # Create environment file
   cp .env.example .env
   # Edit .env with your settings

   # Start services
   docker-compose up -d
   ```

3. **Setup Reverse Proxy (Nginx):**
   ```nginx
   # /etc/nginx/sites-available/document-kb
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## 🔧 Environment Configuration

### Required Environment Variables:
```env
# Essential
OPENAI_API_KEY=sk-...your_key_here

# Optional
USE_LOCAL_MODEL=false
```

### Platform-Specific Setup:

**Streamlit Cloud:**
- Add secrets in dashboard
- Automatic HTTPS
- Custom subdomain available

**Railway/Render:**
- Set environment variables in dashboard
- Automatic HTTPS and domain
- Easy scaling options

**Google Cloud/AWS:**
- Use secret management services
- Configure load balancer for HTTPS
- Set up auto-scaling groups

## 🔐 Security Considerations

### Authentication & User Management:

**New in v2.0:** Multi-user authentication system with:
- Bcrypt password hashing (never stores plaintext passwords)
- Session-based authentication
- Role-based access control (admin/user)
- Per-user data isolation (separate ChromaDB collections)
- Admin panel for user management

### Production Checklist:
- [ ] **Change default admin password immediately**
- [ ] Never commit `.env` files or secrets
- [ ] Use environment variables for all sensitive data
- [ ] Enable HTTPS (handled automatically by most platforms)
- [ ] Set up proper firewall rules (for VPS deployments)
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Review user accounts regularly via admin panel
- [ ] Deactivate unused accounts
- [ ] Implement password rotation policy

### Data Privacy:
- [ ] Document storage is local to your deployment
- [ ] Per-user ChromaDB collections prevent data leakage between users
- [ ] OpenAI API calls follow their data usage policies
- [ ] User database (`users.db`) contains hashed passwords only
- [ ] Consider GDPR/compliance requirements for document storage

### Important Notes for Streamlit Cloud Free Tier:

⚠️ **User Database Persistence:**
- The SQLite user database (`users.db`) is **ephemeral** on free tier
- Database resets when the app restarts/sleeps
- Users will need to re-register after app restarts
- Default admin account is auto-created on each restart

**For Production with Persistent Users:**
1. Upgrade to Streamlit Cloud paid tier with persistent storage
2. Migrate to PostgreSQL or other cloud database
3. Use external authentication service (Auth0, Firebase Auth)

⚠️ **Document Collections:**
- ChromaDB collections are also ephemeral on free tier
- Users need to re-upload documents after restarts
- First load downloads ML models (2-3 minutes)
- For persistence: use paid tier or external vector database

## 📊 Monitoring & Maintenance

### Health Checks:
```bash
# Check application health
curl http://your-domain.com/_stcore/health

# Monitor logs (Docker)
docker-compose logs -f

# Check resource usage
docker stats
```

### Backup Strategy:
```bash
# Backup vector database
tar -czf vectordb-backup-$(date +%Y%m%d).tar.gz vectordb/

# Backup uploaded files
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/
```

## 💰 Cost Estimates

| Platform | Free Tier | Paid Plans | Best For |
|----------|-----------|------------|----------|
| Streamlit Cloud | ✅ Unlimited public apps | $20/month private | Personal projects |
| Railway | $5/month | $20-100/month | Small-medium apps |
| Render | $7/month | $25-85/month | Production apps |
| Google Cloud | $300 credit | $10-50/month | Enterprise |
| AWS | 12 months free | $15-100/month | Large scale |
| VPS (DigitalOcean) | N/A | $5-20/month | Full control |

## 🚨 Troubleshooting

### Common Issues:

**Port Conflicts:**
```bash
# Check what's using port 8501
lsof -i :8501

# Use different port
streamlit run src/app.py --server.port 8502
```

**Memory Issues:**
```bash
# Increase Docker memory limit
docker run -m 2g document-knowledge-base

# Monitor memory usage
docker stats --no-stream
```

**Permission Errors:**
```bash
# Fix file permissions
chmod -R 755 vectordb uploads

# Docker permissions
sudo usermod -aG docker $USER
```

## 🎯 Recommended Approach

**For Personal Use:** Streamlit Cloud
**For Small Team:** Railway or Render
**For Enterprise:** Google Cloud Run or AWS ECS
**For Full Control:** VPS with Docker

## 📞 Support

- Check logs first: `docker-compose logs`
- Test locally before deploying
- Use platform-specific documentation
- Monitor resource usage and costs

Your Document Knowledge Base is now ready to be a live website! 🚀