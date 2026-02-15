# Continuous Learning Pipeline — Knowledge Base Documentation

## Overview

The Continuous Learning Pipeline is an advanced feature that automatically learns from your real legal documents to improve document generation quality. The system scans your local documents, classifies them, extracts key information, and builds learned templates that are used when generating new documents.

## Key Features

### 1. **Automatic Document Discovery & Indexing**
- Recursively scans configured directories for legal documents (.pdf, .docx, .txt, .doc)
- Automatically detects file changes and avoids re-processing
- Extracts text from various document formats
- Indexes documents in ChromaDB for fast semantic search

### 2. **AI-Powered Document Classification**
- Uses your LLM to automatically classify document types
- Extracts key fields, parties, dates, amounts, and other structured data
- Identifies document structure and common sections
- Confidence scoring for classification accuracy

### 3. **Learned Template Generation**
- Aggregates field information across multiple documents of the same type
- Calculates field frequency and confidence scores
- Automatically generates field lists for document types based on real examples
- Prioritizes learned templates over hardcoded defaults

### 4. **Background Scanning Service**
- Runs continuously in a background thread (non-blocking)
- Configurable scan interval (default: 30 minutes)
- Incremental updates — only processes new or modified files
- Real-time progress tracking and status updates

### 5. **Style-Aware Document Generation**
- Uses real document chunks as style examples when generating new documents
- Matches tone, structure, and formatting of your actual documents
- Provides field suggestions based on learned patterns
- "Based on your document library" indicators show when learned templates are used

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit App                        │
│  - UI for Knowledge Base management                     │
│  - Learned template integration                         │
│  - Scanner status and controls                          │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼──────────┐    ┌────────▼─────────┐
│  Document    │    │  Background      │
│  Scanner     │    │  Scanner         │
│  - Discovery │    │  - Threading     │
│  - Extract   │    │  - Scheduling    │
│  - Classify  │    │  - Monitoring    │
│  - Index     │    │                  │
└───┬──────────┘    └──────────────────┘
    │
    ├──────────┬──────────┬─────────────┐
    │          │          │             │
┌───▼────┐  ┌─▼────┐  ┌──▼─────┐  ┌───▼─────┐
│ChromaDB│  │SQLite│  │  LLM   │  │File Sys │
│Vectors │  │ KB   │  │Backend │  │ Watch   │
└────────┘  └──────┘  └────────┘  └─────────┘
```

### Data Flow

1. **Discovery**: Scanner finds documents in configured paths
2. **Extraction**: Text is extracted from PDF, DOCX, TXT files
3. **Classification**: LLM analyzes document to determine type and extract fields
4. **Indexing**: Document chunks stored in ChromaDB with rich metadata
5. **Aggregation**: Fields aggregated across documents to build learned templates
6. **Generation**: New documents use learned templates and style examples

### File Structure

```
/c/Users/SJK/document-knowledge-base/
├── knowledge_db.py              # SQLite database for learned templates
├── document_scanner.py          # Document discovery and indexing
├── background_scanner.py        # Background thread manager
├── knowledge.db                 # SQLite database (gitignored)
├── chroma_db/                   # Vector database (gitignored)
│   └── ... (learned document chunks)
└── streamlit_app.py            # UI integration
```

## Configuration

### Environment Variables (.env)

```bash
# Paths to scan (comma-separated)
SCAN_PATHS=C:/Users/SJK/Documents/,E:/etdocumentsdownload/

# Scan interval in minutes
SCAN_INTERVAL_MINUTES=30

# Auto-start scanner on app launch
AUTO_SCAN_ENABLED=true
```

### Default Scan Paths

1. `C:/Users/SJK/Documents/` — Personal documents folder
2. `E:/etdocumentsdownload/` — Document download folder

You can add additional paths by updating the `SCAN_PATHS` environment variable.

## Usage

### Initial Setup

1. **Configure Scan Paths**: Update `.env` with your document directories
2. **Start the App**: Run `streamlit run streamlit_app.py`
3. **Trigger First Scan**: Click "Scan Now" in the sidebar or Knowledge Base page
4. **Wait for Completion**: First scan may take several minutes depending on document count
5. **Review Templates**: Check the "Learned Templates" tab to see what was discovered

### Accessing the Knowledge Base

1. Click **"📚 Knowledge Base"** in the sidebar
2. View statistics on the dashboard
3. Explore learned templates, indexed documents, scanner settings, and scan history

### Using Learned Templates

When creating a new document:

1. Select a document type from the grid
2. If a learned template exists (3+ real document samples), you'll see:
   - "📚 Learned from your document library" badge
   - Fields marked with confidence scores
   - "Based on X documents" indicators
3. The generated document will use style examples from your real documents

### Manual Scanning

**Sidebar Quick Scan:**
- Click "🔍 Scan Now" in the sidebar

**Knowledge Base Page:**
- Go to Knowledge Base → Scanner Settings
- Click "🔍 Scan Now" to trigger immediate scan
- Click "🔄 Rebuild Templates" to regenerate learned templates from indexed documents

### Managing the Scanner

**Start/Stop:**
```
Knowledge Base → Scanner Settings → ▶️ Start Scanner / ⏸️ Stop Scanner
```

**Adjust Scan Interval:**
```
Knowledge Base → Scanner Settings → Update scan interval
```

**View Progress:**
- Real-time progress shown in sidebar
- Detailed progress in Knowledge Base page

## How It Works

### Document Classification

The LLM analyzes each document to extract:

```json
{
  "document_type": "contract",
  "document_subtype": "Independent Contractor Agreement",
  "confidence": 0.95,
  "extracted_fields": {
    "company_name": "ABC Corporation",
    "contractor_name": "John Doe",
    "start_date": "January 1, 2024",
    "compensation": "$5,000/month",
    ...
  },
  "sections": [
    "Services",
    "Payment Terms",
    "Intellectual Property",
    "Confidentiality",
    "Termination"
  ]
}
```

### Template Learning

For each document type, the system:

1. **Collects all classified documents** of that type
2. **Counts field occurrences** across all documents
3. **Calculates confidence scores** (frequency / total documents)
4. **Generates field definitions** for fields appearing in 30%+ of documents
5. **Stores learned template** in SQLite database

Example learned template:

```python
[
  {
    "key": "company_name",
    "label": "Company Name",
    "type": "text",
    "confidence": 0.95,  # Appears in 95% of documents
    "frequency": 19,      # Found in 19 out of 20 documents
    "learned": True,
    "sample_count": 20
  },
  ...
]
```

### Style Example Retrieval

When generating a new document:

1. Query ChromaDB for chunks with matching `document_type` metadata
2. Score chunks by:
   - Length (longer = more context)
   - Source (scanned documents get priority)
   - Classification confidence
3. Select top 3 chunks as style examples
4. Include in LLM prompt to guide tone and structure

## Database Schema

### SQLite Tables

**learned_templates:**
```sql
id INTEGER PRIMARY KEY
document_type TEXT UNIQUE
fields JSON                  -- Array of field definitions
field_frequencies JSON       -- Field occurrence counts
sample_count INTEGER         -- Number of documents analyzed
last_updated TIMESTAMP
created_at TIMESTAMP
```

**scanned_files:**
```sql
id INTEGER PRIMARY KEY
file_path TEXT UNIQUE
file_hash TEXT              -- SHA-256 for change detection
file_size INTEGER
document_type TEXT
extracted_fields JSON
scan_date TIMESTAMP
status TEXT                 -- 'indexed', 'failed', etc.
```

**scan_history:**
```sql
id INTEGER PRIMARY KEY
scan_start TIMESTAMP
scan_end TIMESTAMP
files_scanned INTEGER
files_indexed INTEGER
files_failed INTEGER
errors TEXT
status TEXT                 -- 'running', 'completed'
```

### ChromaDB Metadata

Each document chunk includes:

```python
{
  "source_path": "/path/to/document.pdf",
  "file_name": "contract.pdf",
  "chunk_index": 0,
  "document_type": "Independent Contractor Agreement",
  "document_type_category": "contract",
  "confidence": 0.95,
  "indexed_date": "2024-01-15T10:30:00",
  "file_size": 102400,
  "file_hash": "abc123..."
}
```

## Performance Considerations

### File Size Limits
- Maximum file size: 10MB
- Files over 10MB are automatically skipped
- Empty files are ignored

### Memory Management
- Text extraction processes files one at a time
- Chunks limited to 800 characters with 100-character overlap
- Background scanner runs in separate thread (non-blocking)

### Scan Performance
- First scan: ~2-5 minutes for 100 documents
- Incremental scans: ~10-30 seconds (only new files)
- LLM classification: ~1-2 seconds per document
- ChromaDB indexing: ~0.1 seconds per document

### Caching
- File hash comparison prevents re-processing unchanged files
- Learned templates cached until updated
- ChromaDB queries are fast (vector similarity search)

## Troubleshooting

### Scanner Not Running

**Check Status:**
```
Sidebar → Knowledge Base status shows "Scanner stopped"
```

**Solutions:**
1. Go to Knowledge Base → Scanner Settings
2. Click "▶️ Start Scanner"
3. Check that scan paths exist and are accessible

### No Documents Indexed

**Possible Causes:**
- Scan paths don't exist or are empty
- File permissions prevent access
- Files are larger than 10MB
- Unsupported file formats

**Check:**
1. Knowledge Base → Scanner Settings → verify scan paths (✅ or ❌)
2. Knowledge Base → Scan History → check for errors
3. Review error messages in scan history

### Low Classification Confidence

If documents are classified with low confidence (<0.5):

**Causes:**
- Document is unusual or custom format
- Document contains limited text
- Document is hybrid/multi-type

**Impact:**
- Document still indexed, but may not contribute to learned templates
- Lower priority in style example selection

**Solutions:**
- Manual review in Knowledge Base → Indexed Documents
- Ensure documents have clear structure and sufficient text

### Learned Templates Not Used

**Requirements for learned templates:**
- Minimum 3 documents of the same type
- Field appears in at least 30% of documents
- Exact document type name match

**Check:**
1. Knowledge Base → Learned Templates
2. Verify sample count >= 3
3. Check field confidence scores

### Performance Issues

If scanning is slow:

**Solutions:**
1. Increase scan interval (reduce frequency)
2. Reduce number of scan paths
3. Exclude large directories with many non-document files
4. Consider stopping scanner during heavy document generation

## Security & Privacy

### Data Storage
- All data stored locally (ChromaDB, SQLite)
- No data sent to external services except LLM API
- Original files not modified or moved

### LLM Processing
- Document excerpts (first ~2000 chars) sent to LLM for classification
- Full document text never leaves your system
- OpenAI: Texts sent to OpenAI API (follow OpenAI privacy policy)
- Ollama: Texts processed locally (fully private)

### File Access
- Scanner uses read-only access
- No write operations on source files
- Respects file system permissions

## Future Enhancements

Potential improvements for future versions:

1. **Multi-language support** for document classification
2. **Custom field extraction patterns** (regex, NER)
3. **Document clustering** to discover new document types
4. **Version tracking** for documents that change over time
5. **Export learned templates** for sharing across installations
6. **Cloud storage integration** (Google Drive, Dropbox, SharePoint)
7. **Incremental learning** (update templates as new documents arrive)
8. **Quality metrics** for generated documents vs. learned examples

## API Reference

### KnowledgeDB

```python
from knowledge_db import KnowledgeDB

kb = KnowledgeDB(db_path="./knowledge.db")

# Get learned template
template = kb.get_learned_template("Independent Contractor Agreement")

# Get statistics
stats = kb.get_stats()

# Get scan history
history = kb.get_scan_history(limit=10)
```

### DocumentScanner

```python
from document_scanner import DocumentScanner

scanner = DocumentScanner(
    llm=llm_backend,
    chroma_collection=collection,
    knowledge_db=knowledge_db,
    scan_paths=["C:/Documents/"]
)

# Run scan
stats = scanner.scan_and_index()

# Build learned templates
scanner.build_learned_templates()
```

### BackgroundScanner

```python
from background_scanner import ScannerManager

# Initialize (once at app startup)
scanner = ScannerManager.initialize(
    llm=llm,
    chroma_collection=collection,
    knowledge_db=knowledge_db,
    scan_interval_minutes=30,
    auto_start=True
)

# Get status
status = scanner.get_status()

# Manual control
scanner.trigger_scan()
scanner.stop()
scanner.start()
```

## Support

For issues or questions:

1. Check this documentation
2. Review scan history for error messages
3. Check application logs
4. Verify scan paths and file permissions
5. Ensure LLM backend is configured and accessible

## License

This feature is part of the Corporate Law Document Generator application.
