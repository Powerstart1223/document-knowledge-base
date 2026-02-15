# Knowledge Base Quick Start Guide

## What is the Continuous Learning Pipeline?

The Continuous Learning Pipeline automatically learns from your real legal documents to improve document generation. It scans your local files, understands what fields are needed for each document type, and uses your actual documents as style examples when generating new ones.

## 5-Minute Setup

### Step 1: Configure Scan Paths (30 seconds)

Edit your `.env` file:

```bash
# Default paths (already configured)
SCAN_PATHS=C:/Users/SJK/Documents/,E:/etdocumentsdownload/

# Optional: Adjust scan interval (default 30 minutes)
SCAN_INTERVAL_MINUTES=30

# Optional: Auto-start on app launch (default true)
AUTO_SCAN_ENABLED=true
```

### Step 2: Start the Application (15 seconds)

```bash
streamlit run streamlit_app.py
```

The background scanner will automatically start and begin discovering documents.

### Step 3: Run Your First Scan (2-5 minutes)

**Option A: Wait for automatic scan**
- Scanner runs every 30 minutes automatically
- Check sidebar for status updates

**Option B: Manual trigger (recommended for first time)**
1. Look at the sidebar
2. Click "🔍 Scan Now" button
3. Watch progress in real-time

### Step 4: View Results (30 seconds)

1. Click "📚 Knowledge Base" in the sidebar
2. See your indexed documents count
3. Check "Learned Templates" tab to see what was discovered

### Step 5: Use Learned Templates (1 minute)

1. Click "Create New Document" from home
2. Select a document type that has been learned (look for the badge)
3. You'll see: "📚 Learned from your document library"
4. Fields will show confidence scores from your real documents
5. Generate document using real examples from your files

## What Gets Scanned?

**File Types:**
- PDF (.pdf)
- Word Documents (.docx, .doc)
- Text Files (.txt)

**What's Skipped:**
- System folders (Windows, Program Files, etc.)
- Files over 10MB
- Hidden folders (starting with .)
- Virtual environments, node_modules, etc.

## How It Learns

For each document:

1. **Extract Text**: Reads PDF, DOCX, or TXT
2. **Classify**: LLM determines what type of document it is
3. **Extract Fields**: Finds parties, dates, amounts, terms, etc.
4. **Index**: Stores in vector database for fast search
5. **Aggregate**: After scanning multiple documents of same type, creates learned template

Example:
- Scans 12 NDAs from your files
- Notices 11/12 have "Disclosing Party" field
- Notices 10/12 have "Receiving Party" field
- Notices 9/12 have "Effective Date" field
- Creates learned template with these fields (91%, 83%, 75% confidence)

## Monitoring Progress

### Sidebar Status
```
📊 Knowledge Base
45 documents indexed
12 document types learned
Last scan: 5 min ago
[🔍 Scan Now]
```

### Knowledge Base Dashboard

Click "📚 Knowledge Base" to see:

**Overview:**
- Total documents indexed
- Document types learned
- Total scans run
- Last scan time

**Learned Templates:**
- Which document types have been learned
- How many real documents each template is based on
- Field confidence scores

**Indexed Documents:**
- Browse by document type
- See which files were indexed
- File size and scan date

**Scanner Settings:**
- Current status (running/stopped)
- Real-time progress during scans
- Manual controls (start/stop/scan now)
- Rebuild templates

**Scan History:**
- Recent scan sessions
- Success/failure statistics
- Duration and error logs

## Tips for Best Results

### 1. Organize Your Files

Good:
```
C:/Documents/Contracts/
  ├── NDAs/
  ├── Employment/
  └── Leases/
```

The scanner will find and classify everything regardless of folder structure, but organization helps you manage files.

### 2. Ensure File Quality

- Documents should have actual text (not just scanned images)
- Clean, professional documents work best
- At least 3-5 examples of each document type for good templates

### 3. Review Learned Templates

After first scan:
1. Go to Knowledge Base → Learned Templates
2. Review what was discovered
3. Check confidence scores
4. If a template seems wrong, you may need more examples

### 4. Use the "Scan Now" Button

Rather than waiting 30 minutes:
- Add new documents to your folders
- Click "Scan Now" to immediately process them
- Templates update automatically

### 5. Monitor for Errors

Check Knowledge Base → Scan History:
- Look for failed files
- Common issues: large files, locked files, permission errors
- Fix issues and re-scan

## Example Workflow

### Day 1: Initial Setup
```
09:00 - Install and configure scan paths
09:05 - Click "Scan Now" — scanner finds 150 documents
09:10 - Review progress in sidebar (processing...)
09:15 - Scan complete! 142 indexed, 8 failed
09:20 - Check Learned Templates — 8 document types discovered
09:25 - Test: Create "NDA" — uses learned template from 15 real NDAs
09:30 - Generated NDA matches style of your actual documents
```

### Ongoing Use
```
Week 1 - Scanner runs every 30 minutes automatically
       - Discovers 20 new documents
       - Updates learned templates

Week 2 - You add 50 new contracts to E:/etdocumentsdownload/
       - Scanner picks them up next cycle
       - Learned "Contract" template improves with more examples

Week 3 - Generate new employment agreement
       - Uses learned template from 25 real employment docs
       - Includes fields that actually appear in YOUR documents
       - Matches YOUR firm's style and tone
```

## Troubleshooting

### "Scanner stopped" in sidebar

**Fix:**
1. Go to Knowledge Base → Scanner Settings
2. Click "▶️ Start Scanner"

### "0 documents indexed"

**Check:**
1. Verify scan paths exist: Knowledge Base → Scanner Settings
2. Look for ✅ next to each path
3. If ❌, update `.env` with correct paths
4. Click "Scan Now" to retry

### "Failed to index X files"

**Review:**
1. Knowledge Base → Scan History
2. Click on the scan session
3. Read error messages
4. Common fixes:
   - Large files: exclude or compress
   - Locked files: close applications using them
   - Permissions: ensure read access

### Templates not being used

**Requirements:**
- Minimum 3 documents of same type
- Field appears in 30%+ of documents
- Exact document type name match

**Check:**
1. Knowledge Base → Learned Templates
2. Find your document type
3. Verify sample count >= 3
4. Check field confidence scores

### Slow scanning

**Optimize:**
1. Increase scan interval: `SCAN_INTERVAL_MINUTES=60`
2. Exclude large folders from `SCAN_PATHS`
3. Temporarily stop scanner during heavy document generation

## What's Next?

Once your knowledge base is populated:

1. **Better Templates**: Generate documents using fields from YOUR real documents
2. **Style Matching**: New documents match YOUR firm's style and tone
3. **Field Intelligence**: Pre-filled suggestions based on common patterns
4. **Continuous Improvement**: As you add documents, templates get better
5. **Zero Manual Work**: Everything happens automatically in the background

## Advanced Configuration

### Custom Scan Paths

Add any directory:
```bash
SCAN_PATHS=C:/MyDocs/,D:/SharedDrive/Legal/,E:/Archive/
```

### Scan on Demand Only

Disable automatic scanning:
```bash
AUTO_SCAN_ENABLED=false
SCAN_INTERVAL_MINUTES=999999
```

Then use "Scan Now" button when needed.

### High-Frequency Scanning

For rapidly changing document libraries:
```bash
SCAN_INTERVAL_MINUTES=5  # Every 5 minutes
```

Note: More frequent scanning uses more CPU.

## Privacy & Security

- All processing happens locally (except LLM API calls)
- Documents never leave your machine
- Only text excerpts sent to LLM for classification
- Original files are never modified
- Use Ollama for fully local processing (no cloud)

## Support

Questions? Check:
1. Full documentation: `KNOWLEDGE_BASE_README.md`
2. Scan History for error messages
3. Knowledge Base dashboard for statistics
4. Sidebar for real-time status

Happy document generating! 📚⚖️
