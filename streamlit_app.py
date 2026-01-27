import streamlit as st
import os
from typing import List
import chromadb
from chromadb.utils import embedding_functions

# Configure Streamlit page
st.set_page_config(
    page_title="Document Knowledge Base",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

# Initialize ChromaDB
@st.cache_resource
def get_chroma_client():
    """Create a persistent ChromaDB client."""
    client = chromadb.PersistentClient(path="./chroma_db")
    return client

@st.cache_resource
def get_embedding_function():
    """Create a sentence-transformers embedding function."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

def get_collection():
    """Get or create the documents collection."""
    client = get_chroma_client()
    ef = get_embedding_function()
    return client.get_or_create_collection(
        name="documents",
        embedding_function=ef,
    )

# Try to configure OpenAI
try:
    import openai

    # Get API key from secrets
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if api_key:
        openai.api_key = api_key
        st.session_state.openai_configured = True
    else:
        st.session_state.openai_configured = False

except Exception as e:
    st.session_state.openai_configured = False
    st.session_state.openai_error = str(e)

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded file"""
    try:
        name = uploaded_file.name.lower()
        if name.endswith(".txt"):
            return str(uploaded_file.read(), "utf-8")
        elif name.endswith(".pdf"):
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif name.endswith(".docx"):
            import docx
            doc = docx.Document(uploaded_file)
            return "\n".join(p.text for p in doc.paragraphs)
        else:
            return "Unsupported file type. Please upload a .txt, .pdf, or .docx file."
    except Exception as e:
        return f"Error reading file: {str(e)}"

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def process_uploaded_files(uploaded_files: List):
    """Process uploaded files: extract text, chunk, and index in ChromaDB."""
    collection = get_collection()
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_chunks = 0
    new_files = 0

    for i, uploaded_file in enumerate(uploaded_files):
        filename = uploaded_file.name

        # Skip files already processed
        if filename in st.session_state.processed_files:
            progress_bar.progress((i + 1) / len(uploaded_files))
            continue

        status_text.text(f"Processing {filename}...")

        try:
            text = extract_text_from_file(uploaded_file)
            chunks = chunk_text(text)

            if chunks:
                ids = [f"{filename}_chunk_{j}" for j in range(len(chunks))]
                metadatas = [{"source": filename, "chunk_index": j} for j in range(len(chunks))]
                collection.add(
                    documents=chunks,
                    ids=ids,
                    metadatas=metadatas,
                )
                total_chunks += len(chunks)
                new_files += 1
                st.session_state.processed_files.add(filename)

            progress_bar.progress((i + 1) / len(uploaded_files))
        except Exception as e:
            st.error(f"Error processing {filename}: {str(e)}")

    if new_files:
        st.success(f"Processed {new_files} file(s) into {total_chunks} chunks.")
    elif uploaded_files:
        st.info("All files have already been processed.")

    progress_bar.empty()
    status_text.empty()

def rag_query(question: str):
    """Retrieve relevant chunks and generate an answer using OpenAI."""
    if not st.session_state.get("openai_configured", False):
        return "OpenAI API key not configured. Please add OPENAI_API_KEY in Streamlit Cloud secrets.", []

    collection = get_collection()

    if collection.count() == 0:
        return "No documents have been indexed yet. Please upload and process documents first.", []

    # Retrieve top 5 most relevant chunks
    results = collection.query(
        query_texts=[question],
        n_results=min(5, collection.count()),
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # Build context with source references
    context_parts = []
    sources = set()
    for doc, meta in zip(documents, metadatas):
        source = meta["source"]
        sources.add(source)
        context_parts.append(f"[Source: {source}]\n{doc}")

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""Answer the question based on the provided context. Reference which source document(s) the information comes from. If the context doesn't contain enough information to answer the question, say so clearly.

Context from uploaded documents:
{context}

Question: {question}

Please provide a helpful answer based on the context above, citing the source document(s):"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1,
        )
        return response.choices[0].message.content, sorted(sources)
    except Exception as e:
        return f"Error generating answer: {str(e)}", []

def main():
    st.title("📚 Document Knowledge Base")
    st.markdown("**RAG-Powered** - Upload documents and ask questions using vector search + AI")

    collection = get_collection()

    # Sidebar for document management
    with st.sidebar:
        st.header("📁 Document Upload")

        # File upload
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=["txt", "pdf", "docx"],
            accept_multiple_files=True,
            help="Upload .txt, .pdf, or .docx files to get started"
        )

        if uploaded_files:
            if st.button("📤 Process Documents", type="primary"):
                process_uploaded_files(uploaded_files)

        st.divider()

        # Stats
        st.subheader("📊 Status")
        chunk_count = collection.count()
        st.metric("Chunks Indexed", chunk_count)
        st.metric("Documents Processed", len(st.session_state.processed_files))

        # Clear database button
        if chunk_count > 0:
            if st.button("🗑️ Clear Database"):
                client = get_chroma_client()
                client.delete_collection("documents")
                st.session_state.processed_files = set()
                st.session_state.messages = []
                st.rerun()

        # API Status
        if st.session_state.get("openai_configured", False):
            st.success("✅ OpenAI API Connected")
        else:
            st.error("❌ OpenAI API Not Configured")
            st.info("💡 Add OPENAI_API_KEY in Streamlit Cloud app settings → Secrets")

        st.divider()

        # Instructions
        st.subheader("📋 How to Use")
        st.markdown("""
        1. **Upload** .txt, .pdf, or .docx files
        2. **Process** them by clicking the button
        3. **Ask questions** in the chat below
        4. **Get AI answers** sourced from relevant document chunks
        """)

    # Main content area
    st.header("💬 Ask Questions About Your Documents")

    # Show help if no documents
    if collection.count() == 0:
        st.info("👋 Welcome! Upload and process some documents in the sidebar to get started.")
        return

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching documents and generating answer..."):
                response, sources = rag_query(prompt)

            st.markdown(response)
            if sources:
                st.caption(f"Sources: {', '.join(sources)}")

            full_response = response
            if sources:
                full_response += f"\n\n*Sources: {', '.join(sources)}*"
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })

if __name__ == "__main__":
    main()
