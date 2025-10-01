# Document Knowledge Base

A RAG (Retrieval-Augmented Generation) system that allows you to upload documents and query them using natural language.

## Features

- Upload multiple document formats (PDF, DOCX, TXT)
- **NetDocuments Integration** - Sync documents directly from your NetDocuments account
- Semantic search through your documents
- AI-powered question answering with source citations
- **🆕 AI Document Drafting** - Generate new documents based on learned writing styles
- **Style Learning** - Automatically analyze and learn from your existing documents
- **Document Export** - Export to TXT, DOCX, and PDF formats
- Easy-to-use web interface built with Streamlit

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key (or set USE_LOCAL_MODEL=true)
   ```

3. **Run the application:**
   ```bash
   streamlit run src/app.py
   ```

4. **Upload documents and start asking questions!**

## NetDocuments Integration

To integrate with your NetDocuments account:

1. **Enable NetDocuments integration:**
   ```bash
   python netdocuments_setup.py
   ```

2. **Or manually configure in .env:**
   ```env
   NETDOCUMENTS_ENABLED=true
   NETDOCUMENTS_CLIENT_ID=your_client_id
   NETDOCUMENTS_CLIENT_SECRET=your_client_secret
   ```

3. **Get API credentials:**
   - Register an app in the NetDocuments Developer Portal
   - Copy your Client ID and Client Secret

4. **Authenticate and sync:**
   - Complete OAuth flow in the web interface
   - Use "Sync Recent" or "Search & Sync" to import documents

## AI Document Drafting

Generate professional documents that match the style of your existing documents:

1. **Learn Writing Styles:**
   - Go to the "Document Drafting" tab
   - Click "Learn Styles from Knowledge Base"
   - The AI analyzes your documents to understand writing patterns

2. **Draft New Documents:**
   - Describe what you want to create
   - Choose document type (or let AI auto-detect)
   - AI generates a document using learned styles and knowledge base context

3. **Refine and Export:**
   - Edit the generated document
   - Get AI suggestions for improvements
   - Export to TXT, DOCX, or PDF formats

### Document Types Supported:
- **Legal Documents** - Contracts, agreements, legal briefs
- **Business Documents** - Proposals, letters, reports
- **Technical Documents** - Specifications, manuals, guides
- **General Documents** - Any other document type

## Project Structure

```
document-knowledge-base/
├── src/               # Main application code
├── data/              # Sample documents
├── uploads/           # User uploaded documents
├── vectordb/          # ChromaDB storage
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## How it Works

1. **Document Processing**: Documents are split into chunks and converted to embeddings
2. **Vector Storage**: Embeddings are stored in ChromaDB for fast similarity search
3. **Query Processing**: User questions are matched against relevant document chunks
4. **AI Generation**: LLM generates answers using the retrieved context with source citations