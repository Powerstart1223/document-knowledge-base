# 🌐 Website Deployment Guide

This guide shows you how to deploy your Document Knowledge Base as a live website using different hosting platforms.

## 🚀 Quick Deployment Options

### Option 1: Streamlit Cloud (Recommended for Beginners)
**🆓 Free | ⚡ Fastest Setup | 🔄 Auto-Deploy**

1. **Prepare Repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Set main file: `src/app.py`

3. **Configure Secrets:**
   - In Streamlit Cloud dashboard → Secrets
   - Copy content from `.streamlit/secrets.toml`
   - Add your actual API keys

4. **Your site will be live at:** `https://your-app-name.streamlit.app`

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
NETDOCUMENTS_ENABLED=false
NETDOCUMENTS_CLIENT_ID=your_client_id
NETDOCUMENTS_CLIENT_SECRET=your_client_secret
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

### Production Checklist:
- [ ] Never commit `.env` files or secrets
- [ ] Use environment variables for all sensitive data
- [ ] Enable HTTPS (handled automatically by most platforms)
- [ ] Set up proper firewall rules (for VPS deployments)
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

### Data Privacy:
- [ ] Document storage is local to your deployment
- [ ] OpenAI API calls follow their data usage policies
- [ ] NetDocuments uses OAuth for secure access
- [ ] Consider data residency requirements

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