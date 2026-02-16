"""
Corporate Law Document Generator — Streamlit Application

Features:
- User authentication (login/registration)
- Per-user data isolation
- Role-based access (admin/user)
- Modern, professional UI
- Three-tab interface: Chat Q&A, Generate Document, Settings
- Admin panel for user management
"""

import os
import hashlib
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from typing import List
from datetime import date
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import chromadb
from chromadb.utils import embedding_functions

from llm_backend import LLMBackend
from document_generator import DocumentGenerator, DOCUMENT_TYPES
from api_clients import SECEdgarClient

# Continuous learning pipeline imports
from knowledge_db import KnowledgeDB
from document_scanner import DocumentScanner
from background_scanner import ScannerManager

# Authentication imports
from auth import AuthManager, init_session_state, require_auth, get_user_collection_name
from auth_ui import (
    render_login_page,
    render_registration_page,
    render_verification_page,
    render_admin_panel,
    render_profile_settings,
    render_auth_sidebar
)
from styles import get_custom_css, render_header, render_footer


# ======================================================================
# Page config
# ======================================================================
st.set_page_config(
    page_title="Corporate Law Document Generator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)


# ======================================================================
# Environment detection and smart defaults
# ======================================================================

def is_streamlit_cloud() -> bool:
    """Detect if running on Streamlit Cloud."""
    return os.getenv("STREAMLIT_SHARING_MODE") is not None or \
           os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud"


def get_default_llm_provider() -> str:
    """Auto-detect best LLM provider based on environment.
    Defaults to Ollama for local deployments — all users share the host's Ollama instance.
    """
    try:
        if "LLM_PROVIDER" in st.secrets:
            return st.secrets.get("LLM_PROVIDER", "ollama")
    except Exception:
        pass

    provider = os.getenv("LLM_PROVIDER", "").lower()
    if provider in ["ollama", "openai"]:
        return provider

    if is_streamlit_cloud():
        return "openai"

    # Default to Ollama for local deployments
    return "ollama"


def get_config_value(key: str, default: str = "") -> str:
    """Get config from Streamlit secrets, then env vars, then default."""
    try:
        if key in st.secrets:
            value = st.secrets[key]
            if value and value not in ["your-api-key-here", "your_openai_api_key_here"]:
                return value
    except Exception:
        pass
    return os.getenv(key, default)


# ======================================================================
# Initialize authentication
# ======================================================================

init_session_state(st.session_state)
auth_manager = AuthManager()


# ======================================================================
# Session state defaults with smart environment detection
# ======================================================================

DEFAULT_PROVIDER = get_default_llm_provider()

_DEFAULTS = {
    "messages": [],
    "processed_files": set(),
    "llm_provider": DEFAULT_PROVIDER,
    "llm_model": (
        get_config_value("OPENAI_MODEL", "gpt-4o-mini")
        if DEFAULT_PROVIDER == "openai"
        else get_config_value("OLLAMA_MODEL", "llama3.1:8b")
    ),
    "llm_base_url": get_config_value("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    "openai_api_key": get_config_value("OPENAI_API_KEY", ""),
    "sec_user_agent": get_config_value("SEC_EDGAR_USER_AGENT", ""),
    "generated_text": "",
    "generated_title": "",
    "onboarding_complete": False,
    "workflow_mode": None,  # None, "create", "edit", or "learn"
    "show_settings": False,
    "show_knowledge_base": False,
}

for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ======================================================================
# ChromaDB setup with per-user collections
# ======================================================================

@st.cache_resource
def get_chroma_client():
    return chromadb.PersistentClient(path="./chroma_db")


@st.cache_resource
def get_embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )


@st.cache_resource
def get_knowledge_db():
    """Get the knowledge database instance."""
    return KnowledgeDB(db_path="./knowledge.db")


@st.cache_resource
def get_background_scanner(user_id: int, _llm, _collection, _knowledge_db):
    """Initialize and get the background scanner for the current user (manual/admin only)."""
    return ScannerManager.initialize(
        user_id=user_id,
        llm=_llm,
        chroma_collection=_collection,
        knowledge_db=_knowledge_db,
        auto_start=False,
    )


def get_collection():
    """Get the ChromaDB collection for the current user."""
    if not require_auth(st.session_state):
        # Fallback for unauthenticated (shouldn't happen)
        collection_name = "documents"
    else:
        user = st.session_state.current_user
        collection_name = get_user_collection_name(user.user_id)

    client = get_chroma_client()
    ef = get_embedding_function()
    return client.get_or_create_collection(name=collection_name, embedding_function=ef)


# ======================================================================
# Helpers — LLM / clients
# ======================================================================

def get_llm() -> LLMBackend:
    """Build an LLMBackend from current session-state settings."""
    if st.session_state.llm_provider == "ollama":
        return LLMBackend(
            provider="ollama",
            model=st.session_state.llm_model,
            base_url=st.session_state.llm_base_url,
        )
    else:
        return LLMBackend(
            provider="openai",
            model=st.session_state.llm_model,
            api_key=st.session_state.openai_api_key,
        )


def get_sec_client() -> SECEdgarClient:
    return SECEdgarClient(user_agent=st.session_state.sec_user_agent)


# ======================================================================
# File processing
# ======================================================================

def extract_text_from_file(uploaded_file) -> str:
    """Extract text from an uploaded .txt, .pdf, or .docx file."""
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
            return "Unsupported file type."
    except Exception as e:
        return f"Error reading file: {e}"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def process_uploaded_files(uploaded_files: List, document_type: str):
    """Extract, chunk, and store uploaded files with document_type metadata."""
    collection = get_collection()
    progress = st.progress(0)
    status = st.empty()
    total_chunks = 0
    new_files = 0

    for i, f in enumerate(uploaded_files):
        filename = f.name
        user_id = st.session_state.current_user.user_id

        status.text(f"Processing {filename}...")
        try:
            text = extract_text_from_file(f)
            if text.startswith("Error reading file:"):
                st.error(text)
                progress.progress((i + 1) / len(uploaded_files))
                continue

            content_hash = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]
            file_key = f"{user_id}_{filename}_{content_hash}"

            if file_key in st.session_state.processed_files:
                progress.progress((i + 1) / len(uploaded_files))
                continue

            chunks = chunk_text(text)
            if chunks:
                ids = [f"u{user_id}_{content_hash}_chunk_{j}" for j in range(len(chunks))]
                metadatas = [
                    {
                        "source": filename,
                        "chunk_index": j,
                        "document_type": document_type,
                        "user_id": user_id,
                        "content_hash": content_hash,
                    }
                    for j in range(len(chunks))
                ]

                try:
                    collection.delete(where={"$and": [{"source": filename}, {"user_id": user_id}]})
                except Exception:
                    pass

                collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
                total_chunks += len(chunks)
                new_files += 1
                st.session_state.processed_files.add(file_key)
            progress.progress((i + 1) / len(uploaded_files))
        except Exception as e:
            st.error(f"Error processing {filename}: {e}")

    if new_files:
        st.toast(f"Processed {new_files} file(s) into {total_chunks} chunks.")
        st.success(f"Processed {new_files} file(s) into {total_chunks} chunks.")
    elif uploaded_files:
        st.info("All files have already been processed.")
    progress.empty()
    status.empty()


# ======================================================================
# RAG query (Chat tab)
# ======================================================================

def rag_query(question: str) -> tuple[str, list[str]]:
    """Retrieve relevant chunks and generate an answer via the configured LLM."""
    collection = get_collection()
    if collection.count() == 0:
        return "No documents indexed yet. Upload and process documents first.", []

    results = collection.query(
        query_texts=[question],
        n_results=min(5, collection.count()),
    )
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    context_parts = []
    sources = set()
    for doc, meta in zip(documents, metadatas):
        source = meta["source"]
        sources.add(source)
        context_parts.append(f"[Source: {source}]\n{doc}")
    context = "\n\n---\n\n".join(context_parts)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful legal research assistant. Answer the user's "
                "question based on the provided document context. Cite which "
                "source document(s) the information comes from. If the context "
                "doesn't contain enough information, say so clearly."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Context from uploaded documents:\n{context}\n\n"
                f"Question: {question}\n\n"
                "Provide a helpful answer citing source document(s):"
            ),
        },
    ]

    try:
        llm = get_llm()
        answer = llm.chat(messages, temperature=0.1, max_tokens=1024)
        return answer, sorted(sources)
    except Exception as e:
        return f"Error generating answer: {e}", []


# ======================================================================
# Database stats helper
# ======================================================================

def get_db_stats() -> dict:
    """Return chunk counts broken down by document_type."""
    collection = get_collection()
    total = collection.count()
    stats = {"total": total}
    if total == 0:
        return stats

    for dtype in list(DOCUMENT_TYPES.keys()) + ["reference"]:
        try:
            qr = collection.query(
                query_texts=["document"],
                n_results=min(total, 1000),
                where={"document_type": dtype},
                include=[],
            )
            stats[dtype] = len(qr["ids"][0]) if qr["ids"] else 0
        except Exception:
            stats[dtype] = 0
    return stats


# ======================================================================
# SIDEBAR
# ======================================================================

def render_sidebar():
    """Render generation-focused sidebar. Operational controls are admin-only."""
    current_user = st.session_state.current_user

    render_auth_sidebar(current_user)

    if current_user.is_admin():
        st.markdown("""
        <div class="card-header">
            Admin
        </div>
        """, unsafe_allow_html=True)

        if st.button("Settings", use_container_width=True, key="sidebar_settings"):
            st.session_state.show_settings = True
            st.rerun()

        if st.button("Knowledge Base", use_container_width=True, key="sidebar_knowledge"):
            st.session_state.show_knowledge_base = True
            st.rerun()

        st.divider()

    llm = get_llm()
    if llm.is_available():
        provider_label = st.session_state.llm_provider.title()
        st.markdown(f"""
        <div class="status-badge status-success">
            <span class="connection-indicator connection-success"></span>
            {provider_label} ({st.session_state.llm_model})
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-badge status-error">
            <span class="connection-indicator connection-error"></span>
            LLM: Not connected
        </div>
        """, unsafe_allow_html=True)



# ======================================================================
# ONBOARDING WIZARD
# ======================================================================

def render_onboarding_wizard():
    """Render the first-run onboarding wizard for API key setup."""
    st.markdown("""
    <div style="max-width: 700px; margin: 2rem auto;">
        <div class="card fade-in">
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎉</div>
                <h1 style="margin-bottom: 0.5rem;">Welcome to Your Document Generator!</h1>
                <p style="color: var(--text-secondary); font-size: 1.1rem;">
                    Let's get you set up in just a minute
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        st.markdown("""
        <div class="card fade-in">
            <h3 style="margin-top: 0;">📋 What This App Does</h3>
            <ul style="line-height: 2; color: var(--text-secondary);">
                <li><strong>Upload Documents:</strong> Add your legal documents to build a knowledge base</li>
                <li><strong>Ask Questions:</strong> Chat with your documents using AI-powered search</li>
                <li><strong>Generate Documents:</strong> Create contracts, memos, briefs, and filings</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card fade-in">
            <h3 style="margin-top: 0;">🔑 Setup Your AI Provider</h3>
            <p style="color: var(--text-secondary);">
                This app needs an AI language model to function. Choose your preferred option:
            </p>
        </div>
        """, unsafe_allow_html=True)

        provider_choice = st.radio(
            "Select your AI provider:",
            options=["ollama", "openai"],
            format_func=lambda x: "Ollama (Recommended — free, runs locally)" if x == "ollama" else "OpenAI (Cloud, requires API key)",
            index=0,
            key="onboarding_provider"
        )

        if provider_choice == "openai":
            st.markdown("""
            <div class="info-card">
                <strong>OpenAI Setup:</strong><br>
                1. Visit <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a><br>
                2. Sign up or log in<br>
                3. Create a new API key<br>
                4. Copy and paste it below
            </div>
            """, unsafe_allow_html=True)

            api_key = st.text_input(
                "Enter your OpenAI API Key:",
                type="password",
                placeholder="sk-proj-...",
                help="Your API key should start with 'sk-'",
                key="onboarding_api_key"
            )

            if api_key:
                if api_key.startswith("sk-") and len(api_key) > 20:
                    st.markdown("""
                    <div class="success-card">
                        ✅ API key format looks valid!
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="warning-card">
                        ⚠️ API key format may be invalid (should start with 'sk-')
                    </div>
                    """, unsafe_allow_html=True)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Save & Continue", type="primary", use_container_width=True, disabled=not api_key):
                    st.session_state.openai_api_key = api_key
                    st.session_state.llm_provider = "openai"
                    st.session_state.llm_model = "gpt-4o-mini"
                    st.session_state.onboarding_complete = True
                    st.toast("✅ OpenAI configured successfully!", icon="✅")
                    st.rerun()

            with col_btn2:
                if st.button("Skip for Now", use_container_width=True):
                    st.session_state.onboarding_complete = True
                    st.rerun()

        else:  # Ollama
            st.markdown("""
            <div class="info-card">
                <strong>Ollama Setup:</strong><br>
                1. Download from <a href="https://ollama.com" target="_blank">ollama.com</a><br>
                2. Install and run Ollama on your computer<br>
                3. Pull a model: <code>ollama pull llama3.1:8b</code><br>
                4. Ollama should be running at http://localhost:11434
            </div>
            """, unsafe_allow_html=True)

            # Check if Ollama is available
            try:
                import requests
                r = requests.get("http://localhost:11434/api/tags", timeout=2)
                if r.status_code == 200:
                    st.markdown("""
                    <div class="success-card">
                        ✅ Ollama detected and running!
                    </div>
                    """, unsafe_allow_html=True)

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("💾 Use Ollama", type="primary", use_container_width=True):
                            st.session_state.llm_provider = "ollama"
                            st.session_state.llm_model = "llama3.1:8b"
                            st.session_state.onboarding_complete = True
                            st.toast("✅ Ollama configured successfully!", icon="✅")
                            st.rerun()
                    with col_btn2:
                        if st.button("Skip for Now", use_container_width=True):
                            st.session_state.onboarding_complete = True
                            st.rerun()
                else:
                    st.markdown("""
                    <div class="warning-card">
                        ⚠️ Ollama not detected. Please install and start Ollama first.
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("Skip for Now", use_container_width=True):
                        st.session_state.onboarding_complete = True
                        st.rerun()
            except Exception:
                st.markdown("""
                <div class="warning-card">
                    ⚠️ Ollama not detected. Please install and start Ollama first.
                </div>
                """, unsafe_allow_html=True)

                if st.button("Skip for Now", use_container_width=True):
                    st.session_state.onboarding_complete = True
                    st.rerun()


# ======================================================================
# TAB 1 — Chat Q&A
# ======================================================================

def render_chat_tab():
    """Render the chat Q&A interface."""
    st.markdown("""
    <div class="card-header">
        💬 Chat with Your Documents
    </div>
    """, unsafe_allow_html=True)

    collection = get_collection()
    if collection.count() == 0:
        # Better empty state with onboarding
        st.markdown("""
        <div style="max-width: 600px; margin: 3rem auto; text-align: center;">
            <div style="font-size: 5rem; margin-bottom: 1.5rem; opacity: 0.6;">📚</div>
            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">
                No Documents Yet
            </h3>
            <p style="color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 2rem;">
                Upload legal documents in the sidebar to start asking questions about them.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Quick guide
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="card">
                <div style="font-size: 2.5rem; text-align: center; margin-bottom: 1rem;">1️⃣</div>
                <h4 style="text-align: center; margin-bottom: 0.5rem;">Upload</h4>
                <p style="text-align: center; color: var(--text-secondary); font-size: 0.9rem;">
                    Add PDF, DOCX, or TXT files using the sidebar
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="card">
                <div style="font-size: 2.5rem; text-align: center; margin-bottom: 1rem;">2️⃣</div>
                <h4 style="text-align: center; margin-bottom: 0.5rem;">Process</h4>
                <p style="text-align: center; color: var(--text-secondary); font-size: 0.9rem;">
                    Click "Process Documents" to index them
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="card">
                <div style="font-size: 2.5rem; text-align: center; margin-bottom: 1rem;">3️⃣</div>
                <h4 style="text-align: center; margin-bottom: 0.5rem;">Ask</h4>
                <p style="text-align: center; color: var(--text-secondary); font-size: 0.9rem;">
                    Ask questions and get AI-powered answers
                </p>
            </div>
            """, unsafe_allow_html=True)
        return

    st.caption("Ask questions about your uploaded documents. The AI will search your knowledge base and provide answers with sources.")

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching documents and generating answer..."):
                response, sources = rag_query(prompt)
            st.markdown(response)
            if sources:
                st.caption(f"📚 Sources: {', '.join(sources)}")
            full = response
            if sources:
                full += f"\n\n*Sources: {', '.join(sources)}*"
            st.session_state.messages.append({"role": "assistant", "content": full})

        # Clear chat button
        if len(st.session_state.messages) > 0:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
                st.rerun()


# ======================================================================
# TAB 2 — Generate Document - Workflow Functions
# ======================================================================

def render_mimic_workflow():
    """Workflow 1: Upload and mimic a reference document."""
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <h3 style="margin-bottom: 0.5rem;">Upload a Reference Document</h3>
        <p style="color: var(--text-secondary);">
            Upload a document you'd like to replicate. The AI will analyze its structure,
            extract key fields, and let you modify values to create a new document in the same style.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # File upload
    uploaded_ref = st.file_uploader(
        "Upload reference document",
        type=["pdf", "docx", "txt"],
        key="mimic_upload",
        help="Upload a document to use as a template"
    )

    if uploaded_ref:
        # Extract text
        with st.spinner("Reading document..."):
            ref_text = extract_text_from_file(uploaded_ref)

        if len(ref_text) < 100:
            st.error("Document appears to be too short or unreadable. Please upload a valid document.")
            return

        st.success(f"✅ Loaded {len(ref_text)} characters from {uploaded_ref.name}")

        # Analyze the document
        if st.button("🔍 Analyze Document Structure", type="primary", use_container_width=True):
            with st.spinner("Analyzing document structure and extracting fields..."):
                llm = get_llm()
                collection = get_collection()
                generator = DocumentGenerator(llm, collection, knowledge_db=get_knowledge_db())
                analysis = generator.analyze_document(ref_text)

                # Store in session state
                st.session_state.mimic_analysis = analysis
                st.session_state.mimic_ref_text = ref_text
                st.toast("✅ Analysis complete!", icon="✅")
                st.rerun()

        # Show analysis results and editable fields
        if "mimic_analysis" in st.session_state:
            analysis = st.session_state.mimic_analysis

            st.divider()
            st.markdown(f"""
            <div class="success-card">
                <strong>📄 Document Type:</strong> {analysis.get('document_subtype', 'Unknown')}<br>
                <strong>🎨 Tone:</strong> {analysis.get('tone', 'formal')}<br>
                <strong>📝 Style:</strong> {analysis.get('style_notes', 'Standard legal document')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### ✏️ Edit Field Values")
            st.caption("Modify the extracted values below. The AI will generate a new document with your changes.")

            # Editable form for extracted fields
            with st.form("mimic_edit_form"):
                user_edits = {}
                key_fields = analysis.get("key_fields", {})

                if not key_fields:
                    st.info("No specific fields were extracted. You can describe changes in the text area below.")
                    user_edits["general_changes"] = st.text_area(
                        "Describe the changes you want to make",
                        placeholder="E.g., Change party names from X to Y, update date to...",
                        height=150
                    )
                else:
                    for field_name, field_value in key_fields.items():
                        user_edits[field_name] = st.text_input(
                            field_name.replace("_", " ").title(),
                            value=str(field_value),
                            key=f"mimic_{field_name}"
                        )

                st.divider()
                submitted = st.form_submit_button(
                    "✨ Generate Document",
                    type="primary",
                    use_container_width=True
                )

                if submitted:
                    with st.spinner("Generating document in the style of your reference..."):
                        llm = get_llm()
                        collection = get_collection()
                        generator = DocumentGenerator(llm, collection, knowledge_db=get_knowledge_db())

                        try:
                            text = generator.generate_from_template(
                                st.session_state.mimic_ref_text,
                                analysis,
                                user_edits
                            )
                            st.session_state.generated_text = text
                            st.session_state.generated_title = f"{analysis.get('document_subtype', 'Document')} (Mimicked)"
                            st.toast("✅ Document generated!", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Generation failed: {e}")


def render_guided_workflow():
    """Workflow 2: AI-guided interactive builder."""
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <h3 style="margin-bottom: 0.5rem;">AI-Guided Document Builder</h3>
        <p style="color: var(--text-secondary);">
            Select a document type and the AI will guide you through all the necessary information
            with contextual questions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state for guided workflow
    if "guided_step" not in st.session_state:
        st.session_state.guided_step = 0
        st.session_state.guided_answers = {}
        st.session_state.guided_fields = []

    # Step 0: Select document type
    if st.session_state.guided_step == 0:
        doc_type = st.selectbox(
            "What type of document do you want to create?",
            options=list(DOCUMENT_TYPES.keys()),
            format_func=lambda k: DOCUMENT_TYPES[k]["label"],
            key="guided_doc_type"
        )

        doc_def = DOCUMENT_TYPES[doc_type]
        st.markdown(f"*{doc_def['description']}*")

        if st.button("Start Building →", type="primary", use_container_width=True):
            st.session_state.guided_step = 1
            st.session_state.guided_doc_type = doc_type
            st.session_state.guided_fields = doc_def["fields"]
            st.session_state.guided_current_field = 0
            st.rerun()

    # Step 1+: Ask questions one by one
    elif st.session_state.guided_step > 0:
        fields = st.session_state.guided_fields
        current_idx = st.session_state.guided_current_field
        doc_type = st.session_state.guided_doc_type

        if current_idx < len(fields):
            # Show progress
            progress = (current_idx) / len(fields)
            st.progress(progress)
            st.caption(f"Question {current_idx + 1} of {len(fields)}")

            field = fields[current_idx]

            st.markdown(f"### {field['label']}")
            if field.get("help"):
                st.caption(field["help"])

            # Show the appropriate input type
            if field.get("type") == "date":
                answer = st.date_input(
                    "Select date",
                    value=date.today(),
                    key=f"guided_q_{current_idx}",
                    label_visibility="collapsed"
                )
            elif field.get("type") == "textarea":
                answer = st.text_area(
                    "Your answer",
                    placeholder=field.get("placeholder", ""),
                    height=150,
                    key=f"guided_q_{current_idx}",
                    label_visibility="collapsed"
                )
            else:
                answer = st.text_input(
                    "Your answer",
                    placeholder=field.get("placeholder", ""),
                    key=f"guided_q_{current_idx}",
                    label_visibility="collapsed"
                )

            col1, col2 = st.columns([1, 1])

            with col1:
                if current_idx > 0:
                    if st.button("← Previous", use_container_width=True):
                        st.session_state.guided_current_field -= 1
                        st.rerun()

            with col2:
                next_label = "Next →" if current_idx < len(fields) - 1 else "Generate Document ✨"
                if st.button(next_label, type="primary", use_container_width=True):
                    # Store answer
                    st.session_state.guided_answers[field["key"]] = answer

                    if current_idx < len(fields) - 1:
                        # Move to next question
                        st.session_state.guided_current_field += 1
                        st.rerun()
                    else:
                        # All questions answered - generate document
                        with st.spinner("Generating your document..."):
                            llm = get_llm()
                            collection = get_collection()
                            generator = DocumentGenerator(llm, collection, knowledge_db=get_knowledge_db())

                            try:
                                text = generator.generate(
                                    doc_type,
                                    st.session_state.guided_answers,
                                    use_sec=False,
                                )
                                st.session_state.generated_text = text
                                st.session_state.generated_title = f"{DOCUMENT_TYPES[doc_type]['label']} — Draft"

                                # Reset guided workflow
                                st.session_state.guided_step = 0
                                st.session_state.guided_answers = {}
                                st.session_state.guided_current_field = 0

                                st.toast("✅ Document generated!", icon="✅")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Generation failed: {e}")

            # Show summary of answers so far
            if st.session_state.guided_answers:
                with st.expander("📋 Review Your Answers"):
                    for key, value in st.session_state.guided_answers.items():
                        if value:
                            st.caption(f"**{key.replace('_', ' ').title()}:** {value}")


def render_quick_workflow():
    """Workflow 3: Quick static form (original workflow)."""
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <h3 style="margin-bottom: 0.5rem;">Quick Generate</h3>
        <p style="color: var(--text-secondary);">
            For users who know exactly what they need. Fill out the form and generate immediately.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Document type selector
    doc_type = st.selectbox(
        "Document type",
        options=list(DOCUMENT_TYPES.keys()),
        format_func=lambda k: DOCUMENT_TYPES[k]["label"],
        key="quick_doc_type",
    )

    doc_def = DOCUMENT_TYPES[doc_type]
    st.markdown(f"*{doc_def['description']}*")

    st.divider()

    # Dynamic form
    params = {}
    with st.form("quick_gen_form"):
        st.markdown("### 📋 Document Details")
        st.caption("Fill in the information below. The AI will use these details to draft your document.")

        for field in doc_def["fields"]:
            key = field["key"]
            label = field["label"]
            ftype = field.get("type", "text")
            placeholder = field.get("placeholder", "")
            help_text = field.get("help", "")

            if ftype == "date":
                params[key] = st.date_input(
                    label,
                    value=date.today(),
                    key=f"quick_{key}",
                    help=help_text if help_text else None
                )
            elif ftype == "textarea":
                params[key] = st.text_area(
                    label,
                    placeholder=placeholder,
                    key=f"quick_{key}",
                    height=120,
                    help=help_text if help_text else "Provide detailed information here"
                )
            else:
                params[key] = st.text_input(
                    label,
                    placeholder=placeholder,
                    key=f"quick_{key}",
                    help=help_text if help_text else None
                )

        st.divider()
        st.markdown("### 🔍 Optional: Enhance with External Data")
        st.caption("Pull additional context from external databases (optional)")

        use_sec = st.checkbox(
            "📊 Include SEC EDGAR data",
            help="Fetch relevant public company filings from SEC EDGAR database",
            key="quick_use_sec"
        )

        st.divider()
        submitted = st.form_submit_button(
            "✨ Generate Document",
            type="primary",
            use_container_width=True,
            help="This may take 30-60 seconds depending on the document complexity"
        )

    if submitted:
        llm = get_llm()
        if not llm.is_available():
            st.error(
                "LLM is not available. Check that Ollama is running or OpenAI key is set in Settings."
            )
            return

        collection = get_collection()
        generator = DocumentGenerator(llm, collection, knowledge_db=get_knowledge_db())
        sec_client = get_sec_client() if use_sec else None

        with st.spinner("Generating document... this may take a moment."):
            try:
                text = generator.generate(
                    doc_type,
                    params,
                    sec_client=sec_client,
                    use_sec=use_sec,
                )
                st.session_state.generated_text = text
                st.session_state.generated_title = (
                    f"{doc_def['label']} — {params.get('party_a', '') or params.get('entity_name', '') or params.get('case_caption', '') or params.get('re', '') or 'Draft'}"
                )
                st.toast("✅ Document generated successfully!", icon="✅")
            except Exception as e:
                st.error(f"Generation failed: {e}")


# ======================================================================
# TAB 2 — Generate Document (Main Function)
# ======================================================================

def render_generate_tab():
    """Render the document generation interface with three workflow options."""
    st.markdown("""
    <div class="card-header">
        📝 Generate Legal Documents
    </div>
    """, unsafe_allow_html=True)

    # Check LLM availability
    llm = get_llm()
    if not llm.is_available():
        st.markdown("""
        <div class="error-card">
            <strong>⚠️ AI Provider Not Configured</strong><br><br>
            To generate documents, you need to configure an AI provider.<br><br>
            <strong>Quick Fix:</strong><br>
            1. Go to the <strong>Settings</strong> tab above<br>
            2. Choose either <strong>OpenAI</strong> (cloud) or <strong>Ollama</strong> (local)<br>
            3. Enter your API key or configure Ollama<br>
            4. Come back here to start generating documents
        </div>
        """, unsafe_allow_html=True)
        return

    # Workflow selection
    st.markdown("""
    <div class="info-card" style="margin-bottom: 1.5rem;">
        💡 <strong>Choose your workflow:</strong> Select how you'd like to generate your document below.
    </div>
    """, unsafe_allow_html=True)

    # Three workflow options as tabs
    workflow_tab1, workflow_tab2, workflow_tab3 = st.tabs([
        "🎨 Mimic a Document",
        "🤖 AI-Guided Builder",
        "⚡ Quick Generate"
    ])

    with workflow_tab1:
        render_mimic_workflow()

    with workflow_tab2:
        render_guided_workflow()

    with workflow_tab3:
        render_quick_workflow()

    # Shared preview & download section (shown when any workflow generates a document)
    if st.session_state.get("generated_text"):
        st.divider()
        st.markdown("""
        <div class="card-header">
            📄 Preview & Edit
        </div>
        """, unsafe_allow_html=True)

        st.caption("Review and edit your generated document below before downloading.")

        # Editable text area
        edited_text = st.text_area(
            "Generated document",
            value=st.session_state.generated_text,
            height=500,
            key="preview_edit",
        )

        # Update session state if user edits
        if edited_text != st.session_state.generated_text:
            st.session_state.generated_text = edited_text

        col1, col2, col3 = st.columns([2, 1, 1])

        with col2:
            if st.button("🔄 Reset", use_container_width=True, help="Clear the generated document"):
                st.session_state.generated_text = ""
                st.session_state.generated_title = ""
                st.rerun()

        with col3:
            docx_bytes = DocumentGenerator.text_to_docx(
                st.session_state.generated_text,
                st.session_state.generated_title,
            )
            safe_name = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_"
                for c in st.session_state.generated_title
            ).strip()
            st.download_button(
                label="⬇️ Download .docx",
                data=docx_bytes,
                file_name=f"{safe_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )


# ======================================================================
# TAB 3 — Settings
# ======================================================================

def render_settings_tab():
    """Render the settings interface."""
    current_user = st.session_state.current_user

    # Show environment info
    if is_streamlit_cloud():
        st.markdown("""
        <div class="info-card">
            ☁️ <strong>Running on Streamlit Cloud</strong><br>
            Use OpenAI provider (Ollama requires local installation).
            Secrets should be configured in the Streamlit Cloud dashboard.
        </div>
        """, unsafe_allow_html=True)

    # Create tabs for different settings sections
    settings_tab1, settings_tab2, settings_tab3, settings_tab4 = st.tabs([
        "🤖 LLM Provider",
        "👤 Profile",
        "🔌 Integrations",
        "👥 Admin" if current_user.is_admin() else "👤 Account"
    ])

    # LLM Provider Settings
    with settings_tab1:
        st.markdown("""
        <div class="card-header">
            🤖 AI Language Model
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="info-card">
            The AI language model powers document generation and Q&A. Choose your preferred provider.
        </div>
        """, unsafe_allow_html=True)

        provider = st.radio(
            "Select AI Provider",
            options=["ollama", "openai"],
            format_func=lambda p: "🏠 Ollama (Free, runs locally)" if p == "ollama" else "☁️ OpenAI (Cloud-based, paid API)",
            index=0 if st.session_state.llm_provider == "ollama" else 1,
            key="settings_provider",
            horizontal=False,
        )

        if provider == "ollama" and is_streamlit_cloud():
            st.markdown("""
            <div class="warning-card">
                ⚠️ <strong>Ollama requires local installation</strong><br>
                Ollama is not available on Streamlit Cloud. Please use OpenAI provider for cloud deployments.
            </div>
            """, unsafe_allow_html=True)

        if provider == "ollama":
            st.markdown("#### Ollama Configuration")
            base_url = st.text_input(
                "Ollama API URL",
                value=st.session_state.llm_base_url,
                key="settings_base_url",
                help="Default: http://localhost:11434/v1"
            )
            tmp_llm = LLMBackend(provider="ollama", base_url=base_url)
            models = tmp_llm.list_models()
            if models:
                model = st.selectbox(
                    "Select Model",
                    options=models,
                    index=models.index(st.session_state.llm_model)
                    if st.session_state.llm_model in models
                    else 0,
                    key="settings_model_select",
                    help="Choose from your installed Ollama models"
                )
                st.success(f"✅ Connected to Ollama • {len(models)} model(s) available")
            else:
                model = st.text_input(
                    "Model name",
                    value=st.session_state.llm_model,
                    key="settings_model_text",
                    placeholder="llama3.1:8b"
                )
                st.error("❌ Could not connect to Ollama. Make sure it's running.")
                st.caption("Start Ollama: `ollama serve` • Install models: `ollama pull llama3.1:8b`")
        else:
            st.markdown("#### OpenAI Configuration")
            st.caption("Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)")
            api_key = st.text_input(
                "OpenAI API Key",
                value=st.session_state.openai_api_key if st.session_state.openai_api_key not in ["", "your-api-key-here"] else "",
                type="password",
                key="settings_openai_key",
                help="Your OpenAI API key (starts with sk-)",
                placeholder="sk-proj-..."
            )
            model_options = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
            current_model = st.session_state.llm_model if st.session_state.llm_provider == "openai" else "gpt-4o-mini"
            model = st.selectbox(
                "Model",
                options=model_options,
                index=model_options.index(current_model) if current_model in model_options else 0,
                key="settings_openai_model",
                help="gpt-4o-mini recommended for best cost/performance",
            )
            base_url = "https://api.openai.com/v1"

            if api_key:
                if api_key.startswith("sk-") and len(api_key) > 20:
                    st.success("✅ API key format looks valid")
                else:
                    st.warning("⚠️ API key format may be invalid (should start with 'sk-')")

        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            st.session_state.llm_provider = provider
            st.session_state.llm_model = model
            st.session_state.llm_base_url = base_url
            if provider == "openai":
                st.session_state.openai_api_key = api_key
            st.toast("✅ Settings saved successfully!", icon="✅")
            st.success("AI provider settings saved successfully.")
            st.rerun()

    # Profile Settings
    with settings_tab2:
        render_profile_settings(auth_manager, current_user)

    # Integrations
    with settings_tab3:
        st.markdown("""
        <div class="card-header">
            🔌 External Integrations
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="info-card">
            Configure external data sources to enhance document generation with real-world data.
        </div>
        """, unsafe_allow_html=True)

        # SEC EDGAR
        st.markdown("### 📊 SEC EDGAR")
        st.caption(
            "The SEC EDGAR database provides free access to company filings. "
            "Useful for corporate filings and contracts."
        )
        sec_ua = st.text_input(
            "User-Agent (Your Name + Email)",
            value=st.session_state.sec_user_agent,
            placeholder="John Doe john.doe@lawfirm.com",
            help="SEC requires a User-Agent header with your name and email for API access.",
            key="settings_sec_ua",
        )
        if st.button("💾 Save SEC EDGAR Settings", use_container_width=True):
            st.session_state.sec_user_agent = sec_ua
            st.toast("✅ SEC EDGAR settings saved!", icon="✅")
            st.success("SEC EDGAR settings saved successfully.")

    # Admin Panel or Account Info
    with settings_tab4:
        if current_user.is_admin():
            render_admin_panel(auth_manager, current_user)
        else:
            st.markdown("""
            <div class="info-card">
                ℹ️ <strong>User Account</strong><br>
                You are logged in as a regular user. Contact an administrator for account-related requests.
            </div>
            """, unsafe_allow_html=True)


# ======================================================================
# NEW WORKFLOW: Two-Path Landing Page
# ======================================================================

def render_landing_page():
    """Post-login generation workspace focused on three primary tasks."""
    st.markdown("## Document Workspace")
    st.caption("Choose one of three tasks to continue.")

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("""
        <div class="card" style="padding: 1.2rem; min-height: 210px;">
            <h3 style="margin-top: 0;">New Document</h3>
            <p style="color: var(--text-secondary); line-height: 1.5;">
                Create a new legal document with your saved configuration preferences.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("New Document", type="primary", use_container_width=True, key="home_new_doc"):
            st.session_state.workflow_mode = "create"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="card" style="padding: 1.2rem; min-height: 210px;">
            <h3 style="margin-top: 0;">Review / Manage Existing</h3>
            <p style="color: var(--text-secondary); line-height: 1.5;">
                Edit an uploaded document in-screen with live prompting and export results.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Review / Manage", type="primary", use_container_width=True, key="home_review_doc"):
            st.session_state.workflow_mode = "edit"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="card" style="padding: 1.2rem; min-height: 210px;">
            <h3 style="margin-top: 0;">Learn from a Document</h3>
            <p style="color: var(--text-secondary); line-height: 1.5;">
                Upload examples to improve retrieval and future draft quality.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Learn from Document", type="primary", use_container_width=True, key="home_learn_doc"):
            st.session_state.workflow_mode = "learn"
            st.rerun()


# ======================================================================
# PATH A: Edit Existing Document Workflow
# ======================================================================

def render_edit_workflow():
    """Executive edit flow with intent presets and checkpointed revisions."""

    if st.button("Back to Home", key="back_from_edit"):
        st.session_state.workflow_mode = None
        st.session_state.pop("edit_document_text", None)
        st.session_state.pop("edit_document_history", None)
        st.session_state.pop("edit_chat_messages", None)
        st.session_state.pop("edit_revision_goal", None)
        st.rerun()

    st.markdown("## Edit Existing Document")
    st.caption("Step 1 upload, Step 2 set revision objective, Step 3 apply targeted AI changes.")

    if "edit_revision_goal" not in st.session_state:
        st.session_state.edit_revision_goal = "Preserve structure; improve precision and legal clarity."

    if "edit_document_text" not in st.session_state:
        st.progress(0.33)
        st.markdown("""
        <div class="info-card">
            Upload one document to begin. The assistant maintains full-document continuity for each revision.
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload document",
            type=["pdf", "docx", "txt"],
            key="edit_upload",
            help="Supported: PDF, DOCX, TXT"
        )

        if uploaded_file:
            with st.spinner("Reading document..."):
                text = extract_text_from_file(uploaded_file)

            if len(text) < 50:
                st.error("Document appears too short or unreadable. Upload a valid file.")
            else:
                st.session_state.edit_document_text = text
                st.session_state.edit_document_original = text
                st.session_state.edit_document_history = [{"version": 0, "text": text, "change": "Original document"}]
                st.session_state.edit_chat_messages = []
                st.session_state.edit_filename = uploaded_file.name
                st.session_state.edit_file_ext = ("." + uploaded_file.name.split(".")[-1].lower()) if "." in uploaded_file.name else ".txt"
                st.success(f"Loaded {uploaded_file.name}")
                st.rerun()
        return

    st.progress(0.66)
    st.markdown(f"""
    <div class="info-card">
        <strong>Document:</strong> {st.session_state.get('edit_filename', 'Untitled')}<br>
        <strong>Version:</strong> {len(st.session_state.edit_document_history)}<br>
        <strong>Length:</strong> {len(st.session_state.edit_document_text)} characters
    </div>
    """, unsafe_allow_html=True)

    preset_col, objective_col = st.columns([2, 3], gap="large")
    with preset_col:
        st.markdown("#### Revision Preset")
        preset = st.radio(
            "Choose preset",
            options=["Tighten", "Formalize", "Clarify", "Shorten", "Custom"],
            index=4,
            key="edit_preset_radio",
            label_visibility="collapsed"
        )
        if preset == "Tighten":
            st.session_state.edit_revision_goal = "Reduce verbosity and tighten clause language without changing legal meaning."
        elif preset == "Formalize":
            st.session_state.edit_revision_goal = "Use formal legal register and improve professional tone."
        elif preset == "Clarify":
            st.session_state.edit_revision_goal = "Clarify ambiguous provisions and improve definitional precision."
        elif preset == "Shorten":
            st.session_state.edit_revision_goal = "Shorten text where possible while preserving obligations and risk protections."

    with objective_col:
        st.markdown("#### Current Objective")
        st.session_state.edit_revision_goal = st.text_area(
            "Revision objective",
            value=st.session_state.edit_revision_goal,
            height=120,
            label_visibility="collapsed",
            key="edit_goal_area",
            help="This objective is applied to each AI revision request."
        )
        if len(st.session_state.edit_revision_goal.strip()) < 12:
            st.caption("Add more detail for higher-quality revisions.")

    col_preview, col_ai = st.columns([3, 2], gap="large")

    with col_preview:
        st.markdown("### Working Draft")
        edited_text = st.text_area(
            "Working draft",
            value=st.session_state.edit_document_text,
            height=560,
            key="edit_preview_area",
            label_visibility="collapsed"
        )
        if edited_text != st.session_state.edit_document_text:
            st.session_state.edit_document_text = edited_text

        a, b, c = st.columns(3)
        with a:
            if len(st.session_state.edit_document_history) > 1 and st.button("Undo", use_container_width=True, key="edit_undo"):
                st.session_state.edit_document_history.pop()
                st.session_state.edit_document_text = st.session_state.edit_document_history[-1]["text"]
                st.rerun()
        with b:
            original_name = st.session_state.get("edit_filename", "document")
            ext = st.session_state.get("edit_file_ext", ".txt")
            base_name = original_name.rsplit(".", 1)[0] if "." in original_name else original_name

            if ext == ".txt":
                st.download_button(
                    label="Download .txt",
                    data=st.session_state.edit_document_text.encode("utf-8"),
                    file_name=f"{base_name}_edited.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            else:
                docx_bytes = DocumentGenerator.text_to_docx(
                    st.session_state.edit_document_text,
                    original_name
                )
                st.download_button(
                    label="Download .docx",
                    data=docx_bytes,
                    file_name=f"{base_name}_edited.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
                if ext == ".pdf":
                    st.caption("Original was PDF. Export is provided as editable DOCX.")
        with c:
            if st.button("Reset", use_container_width=True, key="edit_reset"):
                st.session_state.pop("edit_document_text", None)
                st.session_state.pop("edit_document_history", None)
                st.session_state.pop("edit_chat_messages", None)
                st.rerun()

        if len(st.session_state.edit_document_history) > 1:
            with st.expander("Revision checkpoints"):
                for version in reversed(st.session_state.edit_document_history):
                    st.caption(f"v{version['version']}: {version['change']}")

    with col_ai:
        st.markdown("### AI Revision Assistant")
        st.caption("Use specific instructions. The assistant returns a full revised document each time.")

        q1, q2 = st.columns(2)
        with q1:
            if st.button("Strengthen indemnity", use_container_width=True, key="edit_quick_indemnity"):
                st.session_state.edit_chat_messages.append({"role": "user", "content": "Strengthen indemnity language and tighten risk allocation."})
        with q2:
            if st.button("Clarify termination", use_container_width=True, key="edit_quick_termination"):
                st.session_state.edit_chat_messages.append({"role": "user", "content": "Clarify termination triggers and cure periods."})

        for msg in st.session_state.edit_chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Example: Clarify notice mechanics and align defined terms"):
            st.session_state.edit_chat_messages.append({"role": "user", "content": prompt})

        if st.session_state.edit_chat_messages and st.session_state.edit_chat_messages[-1]["role"] == "user":
            pending_prompt = st.session_state.edit_chat_messages[-1]["content"]
            with st.chat_message("assistant"):
                with st.spinner("Applying revision..."):
                    llm = get_llm()
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are a legal document editing assistant. Return the FULL revised document. "
                                "Preserve enforceability and structure unless explicitly asked to alter them."
                            )
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Revision objective: {st.session_state.edit_revision_goal}\n\n"
                                f"Current document:\n\n{st.session_state.edit_document_text}\n\n"
                                f"Change request: {pending_prompt}\n\n"
                                "Return only the full updated document text."
                            )
                        }
                    ]
                    try:
                        response = llm.chat(messages, temperature=0.2, max_tokens=4096)
                        version_num = len(st.session_state.edit_document_history)
                        st.session_state.edit_document_text = response
                        st.session_state.edit_document_history.append({
                            "version": version_num,
                            "text": response,
                            "change": pending_prompt[:72] + ("..." if len(pending_prompt) > 72 else "")
                        })
                        st.session_state.edit_chat_messages.append({"role": "assistant", "content": "Revision applied."})
                        st.rerun()
                    except Exception as e:
                        err = f"Error: {e}"
                        st.error(err)
                        st.session_state.edit_chat_messages.append({"role": "assistant", "content": err})


# ======================================================================
# PATH B: Create New Document Workflow
# ======================================================================

def render_create_workflow():
    """Create flow with short setup wizard + guided drafting workspace."""

    if st.button("Back to Home", key="back_from_create"):
        st.session_state.workflow_mode = None
        for k in [
            "create_setup_complete", "create_setup_goal", "create_setup_style", "create_setup_guidance",
            "create_doc_type", "create_doc_type_label", "create_fields", "create_generated_text", "create_chat_messages"
        ]:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown("## Create New Document")
    st.caption("Hybrid guidance: quick setup, targeted fact capture, then focused drafting.")

    if not st.session_state.get("create_setup_complete", False):
        st.progress(0.33)
        st.markdown("""
        <div class="info-card">
            <strong>Step 1 of 3:</strong> Set drafting defaults. You can revise these later.
        </div>
        """, unsafe_allow_html=True)

        with st.form("create_setup_form"):
            goal = st.selectbox(
                "Drafting goal",
                ["Board-ready first draft", "Client-ready polished draft", "Fast internal draft"],
                index=0,
                help="Controls drafting strictness and polish level."
            )
            style_pref = st.selectbox(
                "Style source",
                ["Learned templates first (recommended)", "Standard template library", "Custom freeform"],
                index=0,
                help="Controls how much the assistant relies on known template patterns."
            )
            guidance_pref = st.selectbox("Guidance level", ["Inline guidance", "Minimal guidance"], index=0)

            submitted = st.form_submit_button("Continue", type="primary", use_container_width=True)
            if submitted:
                st.session_state.create_setup_complete = True
                st.session_state.create_setup_goal = goal
                st.session_state.create_setup_style = style_pref
                st.session_state.create_setup_guidance = guidance_pref
                st.rerun()
        return

    if "create_doc_type" not in st.session_state:
        st.progress(0.66)
        st.markdown("""
        <div class="info-card">
            <strong>Step 2 of 3:</strong> Select document type.
        </div>
        """, unsafe_allow_html=True)

        search_query = st.text_input(
            "Search document types",
            placeholder="employment, lease, nda, board resolution",
            key="doc_type_search_exec"
        ).strip().lower()

        doc_options = list(DOCUMENT_TYPES.keys()) + ["custom_document"]
        filtered = [
            d for d in doc_options
            if not search_query
            or search_query in d.lower()
            or (d in DOCUMENT_TYPES and search_query in DOCUMENT_TYPES[d]["label"].lower())
        ]
        if not filtered:
            st.warning("No document types match your search.")
            return

        selected = st.selectbox(
            "Document type",
            options=filtered,
            format_func=lambda d: "Custom Document" if d == "custom_document" else DOCUMENT_TYPES[d]["label"],
            key="create_doc_type_pick"
        )

        if selected == "custom_document":
            st.caption("Describe requirements and generate a custom legal draft.")
        else:
            st.caption(DOCUMENT_TYPES[selected]["description"])

        if st.button("Use This Document Type", type="primary", use_container_width=True, key="create_doc_type_confirm"):
            if selected == "custom_document":
                st.session_state.create_doc_type = selected
                st.session_state.create_doc_type_label = "Custom Document"
                with st.spinner("Loading dynamic template fields..."):
                    llm = get_llm()
                    generator = DocumentGenerator(llm, get_collection(), knowledge_db=get_knowledge_db())
                    fields = generator.get_required_fields_for_type("Custom Document")
                    st.session_state.create_fields = fields
                    st.session_state.create_is_learned = any(f.get("learned") for f in fields)
            else:
                st.session_state.create_doc_type = selected
                st.session_state.create_doc_type_label = DOCUMENT_TYPES[selected]["label"]
                st.session_state.create_fields = DOCUMENT_TYPES[selected]["fields"]
                st.session_state.create_is_learned = False
            st.rerun()
        return

    if "create_generated_text" not in st.session_state:
        st.progress(1.0)
        st.markdown("""
        <div class="info-card">
            <strong>Step 3 of 3:</strong> Provide key facts. Leave unknown values blank and revise after generation.
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <strong>Drafting goal:</strong> {st.session_state.get('create_setup_goal')}<br>
            <strong>Style source:</strong> {st.session_state.get('create_setup_style')}<br>
            <strong>Guidance:</strong> {st.session_state.get('create_setup_guidance')}
        </div>
        """, unsafe_allow_html=True)

        with st.form("create_doc_form"):
            form_data = {}
            fields = st.session_state.create_fields
            st.caption(f"Complete the fields that are known now. Total fields: {len(fields)}")

            for field in fields:
                key = field.get("key", "field")
                label = field.get("label", key.replace("_", " ").title())
                field_type = field.get("type", "text")
                placeholder = field.get("placeholder", "")
                help_text = field.get("help", "")

                if field_type == "date":
                    form_data[key] = st.date_input(label, value=date.today(), key=f"create_{key}", help=help_text)
                elif field_type == "textarea":
                    form_data[key] = st.text_area(label, placeholder=placeholder, height=100, key=f"create_{key}", help=help_text)
                else:
                    form_data[key] = st.text_input(label, placeholder=placeholder, key=f"create_{key}", help=help_text)

            submitted = st.form_submit_button("Generate Draft", type="primary", use_container_width=True)
            if submitted:
                llm = get_llm()
                if not llm.is_available():
                    st.error("LLM is not available. Check Settings.")
                else:
                    with st.spinner("Generating draft..."):
                        try:
                            collection = get_collection()
                            generator = DocumentGenerator(llm, collection, knowledge_db=get_knowledge_db())
                            doc_type = st.session_state.create_doc_type

                            generation_context = {
                                "draft_goal": st.session_state.get("create_setup_goal", ""),
                                "style_source": st.session_state.get("create_setup_style", ""),
                                "guidance_level": st.session_state.get("create_setup_guidance", ""),
                            }
                            form_payload = {**form_data, **generation_context}

                            if doc_type in DOCUMENT_TYPES:
                                text_out = generator.generate(doc_type, form_payload, use_sec=False)
                            else:
                                system_prompt = (
                                    "You are a legal document drafting assistant. Generate a professional legal draft "
                                    "using formal, structured language. This draft is for attorney review, not legal advice."
                                )
                                params = "\n".join([f"{k}: {v}" for k, v in form_payload.items() if v])
                                user_prompt = f"Generate a {st.session_state.create_doc_type_label} with:\n\n{params}"
                                text_out = llm.generate_document(system_prompt, user_prompt)

                            st.session_state.create_generated_text = text_out
                            st.session_state.create_chat_messages = []
                            st.rerun()
                        except Exception as e:
                            st.error(f"Generation failed: {e}")
        return

    st.markdown(f"""
    <div class="info-card">
        <strong>Draft:</strong> {st.session_state.create_doc_type_label}<br>
        <strong>Objective:</strong> {st.session_state.get('create_setup_goal')}
    </div>
    """, unsafe_allow_html=True)

    col_preview, col_ai = st.columns([3, 2], gap="large")
    with col_preview:
        st.markdown("### Draft Workspace")
        edited_text = st.text_area(
            "Draft",
            value=st.session_state.create_generated_text,
            height=560,
            key="create_preview_area",
            label_visibility="collapsed"
        )
        if edited_text != st.session_state.create_generated_text:
            st.session_state.create_generated_text = edited_text

        a, b, c = st.columns(3)
        with a:
            if st.button("Start Over", use_container_width=True, key="create_start_over_exec"):
                for k in ["create_doc_type", "create_fields", "create_generated_text", "create_chat_messages"]:
                    st.session_state.pop(k, None)
                st.rerun()
        with b:
            docx_bytes = DocumentGenerator.text_to_docx(
                st.session_state.create_generated_text,
                st.session_state.create_doc_type_label
            )
            st.download_button(
                label="Download .docx",
                data=docx_bytes,
                file_name=f"{st.session_state.create_doc_type_label.replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with c:
            if st.button("Re-run Guidance", use_container_width=True, key="create_rerun_setup"):
                st.session_state.create_setup_complete = False
                st.rerun()

    with col_ai:
        st.markdown("### AI Revision Assistant")
        st.caption("Request targeted improvements. The assistant returns a full updated draft.")

        q1, q2 = st.columns(2)
        with q1:
            if st.button("Sharpen recitals", use_container_width=True, key="create_quick_recitals"):
                st.session_state.create_chat_messages.append({"role": "user", "content": "Sharpen recitals and improve narrative clarity without changing legal effect."})
        with q2:
            if st.button("Harden remedies", use_container_width=True, key="create_quick_remedies"):
                st.session_state.create_chat_messages.append({"role": "user", "content": "Harden remedies and default provisions while keeping the current structure."})

        for msg in st.session_state.get("create_chat_messages", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Example: tighten indemnity language and simplify definitions"):
            if "create_chat_messages" not in st.session_state:
                st.session_state.create_chat_messages = []
            st.session_state.create_chat_messages.append({"role": "user", "content": prompt})

        if st.session_state.get("create_chat_messages") and st.session_state.create_chat_messages[-1]["role"] == "user":
            pending_prompt = st.session_state.create_chat_messages[-1]["content"]
            with st.chat_message("assistant"):
                with st.spinner("Applying revisions..."):
                    llm = get_llm()
                    messages = [
                        {
                            "role": "system",
                            "content": "You are a legal document editing assistant. Apply requested changes and return the FULL updated document."
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Draft objective: {st.session_state.get('create_setup_goal')}\n\n"
                                f"Current document:\n\n{st.session_state.create_generated_text}\n\n"
                                f"Revision request: {pending_prompt}\n\n"
                                "Return only the full updated document."
                            )
                        }
                    ]
                    try:
                        response = llm.chat(messages, temperature=0.2, max_tokens=4096)
                        st.session_state.create_generated_text = response
                        st.session_state.create_chat_messages.append({"role": "assistant", "content": "Revision applied."})
                        st.rerun()
                    except Exception as e:
                        err = f"Error: {e}"
                        st.error(err)
                        st.session_state.create_chat_messages.append({"role": "assistant", "content": err})


# ======================================================================
# PATH C: Learn from a Document Workflow
# ======================================================================

def render_learn_workflow():
    """Learn from uploaded documents to improve future generation quality."""

    if st.button("Back to Home", key="back_from_learn"):
        st.session_state.workflow_mode = None
        st.rerun()

    st.markdown("## Learn from a Document")
    st.caption("Upload examples to enrich your knowledge base and improve drafting relevance.")

    uploaded_files = st.file_uploader(
        "Upload one or more documents",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="learn_upload_docs",
        help="These files will be indexed for retrieval and style matching.",
    )

    doc_type = st.selectbox(
        "Learning category",
        options=["reference"] + list(DOCUMENT_TYPES.keys()),
        format_func=lambda x: "Reference (general)" if x == "reference" else DOCUMENT_TYPES[x]["label"],
        key="learn_doc_type",
    )

    if uploaded_files and st.button("Learn from Uploaded Documents", type="primary", use_container_width=True, key="learn_process_btn"):
        process_uploaded_files(uploaded_files, document_type=doc_type)
        st.success("Learning completed. These documents are now available for retrieval.")


# ======================================================================
# Settings Page (Accessed from Sidebar)
# ======================================================================

def render_settings_page():
    """Render the full settings page."""

    # Back button
    if st.button("← Back", key="back_from_settings"):
        st.session_state.show_settings = False
        st.rerun()

    st.markdown("""
    <div class="card-header">
        ⚙️ Settings
    </div>
    """, unsafe_allow_html=True)

    current_user = st.session_state.current_user

    # Create tabs for different settings sections
    settings_tab1, settings_tab2, settings_tab3 = st.tabs([
        "🤖 LLM Provider",
        "👤 Profile",
        "👥 Admin" if current_user.is_admin() else "ℹ️ Info"
    ])

    # LLM Provider Settings
    with settings_tab1:
        st.markdown("""
        <div class="info-card">
            The AI language model powers document generation and editing. Choose your preferred provider.
        </div>
        """, unsafe_allow_html=True)

        provider = st.radio(
            "Select AI Provider",
            options=["ollama", "openai"],
            format_func=lambda p: "🏠 Ollama (Free, runs locally)" if p == "ollama" else "☁️ OpenAI (Cloud-based, paid API)",
            index=0 if st.session_state.llm_provider == "ollama" else 1,
            key="settings_provider",
        )

        if provider == "ollama":
            st.markdown("#### Ollama Configuration")
            base_url = st.text_input(
                "Ollama API URL",
                value=st.session_state.llm_base_url,
                key="settings_base_url",
                help="Default: http://localhost:11434/v1"
            )
            tmp_llm = LLMBackend(provider="ollama", base_url=base_url)
            models = tmp_llm.list_models()
            if models:
                model = st.selectbox(
                    "Select Model",
                    options=models,
                    index=models.index(st.session_state.llm_model)
                    if st.session_state.llm_model in models
                    else 0,
                    key="settings_model_select",
                )
                st.success(f"✅ Connected • {len(models)} model(s) available")
            else:
                model = st.text_input(
                    "Model name",
                    value=st.session_state.llm_model,
                    key="settings_model_text",
                    placeholder="llama3.1:8b"
                )
                st.error("❌ Could not connect to Ollama. Make sure it's running.")
        else:
            st.markdown("#### OpenAI Configuration")
            api_key = st.text_input(
                "OpenAI API Key",
                value=st.session_state.openai_api_key if st.session_state.openai_api_key not in ["", "your-api-key-here"] else "",
                type="password",
                key="settings_openai_key",
                placeholder="sk-proj-..."
            )
            model_options = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
            current_model = st.session_state.llm_model if st.session_state.llm_provider == "openai" else "gpt-4o-mini"
            model = st.selectbox(
                "Model",
                options=model_options,
                index=model_options.index(current_model) if current_model in model_options else 0,
                key="settings_openai_model",
            )
            base_url = "https://api.openai.com/v1"

            if api_key and api_key.startswith("sk-") and len(api_key) > 20:
                st.success("✅ API key format looks valid")

        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            st.session_state.llm_provider = provider
            st.session_state.llm_model = model
            st.session_state.llm_base_url = base_url
            if provider == "openai":
                st.session_state.openai_api_key = api_key
            st.toast("✅ Settings saved!", icon="✅")
            st.success("AI provider settings saved successfully.")
            st.rerun()

    # Profile Settings
    with settings_tab2:
        render_profile_settings(auth_manager, current_user)

    # Admin Panel or Info
    with settings_tab3:
        if current_user.is_admin():
            render_admin_panel(auth_manager, current_user)
        else:
            st.markdown("""
            <div class="info-card">
                <strong>Corporate Law Document Generator</strong><br><br>
                You are logged in as a regular user.<br>
                Contact an administrator for account-related requests.
            </div>
            """, unsafe_allow_html=True)


# ======================================================================
# Knowledge Base Page
# ======================================================================

def render_knowledge_base_page():
    """Render the Knowledge Base management page."""

    current_user = st.session_state.current_user
    if not current_user.is_admin():
        st.error("Access denied. Knowledge Base management is admin-only.")
        return

    # Back button
    if st.button("← Back", key="back_from_kb"):
        st.session_state.show_knowledge_base = False
        st.rerun()

    st.markdown("""
    <div class="card-header">
        📚 Knowledge Base & Continuous Learning
    </div>
    """, unsafe_allow_html=True)

    knowledge_db = get_knowledge_db()
    # Lazy-init scanner only on Knowledge Base page (admin/manual use).
    scanner = ScannerManager.get_instance(current_user.user_id)
    if scanner is None:
        try:
            scanner = get_background_scanner(current_user.user_id, get_llm(), get_collection(), knowledge_db)
        except Exception as e:
            logger.error(f"Failed to initialize scanner on KB page: {e}")
            scanner = None

    stats = knowledge_db.get_stats(user_id=current_user.user_id)

    # Overview stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Documents Indexed", stats["total_documents"])

    with col2:
        st.metric("Document Types", stats["document_types"])

    with col3:
        st.metric("Total Scans", stats["total_scans"])

    with col4:
        if stats["last_scan"]:
            try:
                import dateutil.parser
                import datetime
                last_scan = dateutil.parser.parse(stats["last_scan"])
                time_ago = datetime.datetime.now(datetime.timezone.utc) - last_scan
                hours_ago = int(time_ago.total_seconds() / 3600)
                st.metric("Last Scan", f"{hours_ago}h ago")
            except:
                st.metric("Last Scan", "Recently")
        else:
            st.metric("Last Scan", "Never")

    st.divider()

    # Tabs for different sections
    kb_tab1, kb_tab2, kb_tab3, kb_tab4 = st.tabs([
        "📖 Learned Templates",
        "📁 Indexed Documents",
        "⚙️ Scanner Settings",
        "📊 Scan History"
    ])

    # Tab 1: Learned Templates
    with kb_tab1:
        st.markdown("### Learned Document Templates")
        st.caption("Templates automatically learned from your real documents")

        doc_types = knowledge_db.get_all_document_types(user_id=current_user.user_id)

        if not doc_types:
            st.info("No learned templates yet. Run a scan to build templates from your documents.")
        else:
            for type_info in doc_types:
                doc_type = type_info["type"]
                count = type_info["count"]

                with st.expander(f"📄 {doc_type} — Learned from {count} documents"):
                    learned = knowledge_db.get_learned_template(doc_type, user_id=current_user.user_id)

                    if learned:
                        st.caption(f"Last updated: {learned['last_updated']}")

                        st.markdown("**Learned Fields:**")
                        for field in learned["fields"]:
                            confidence = field.get("confidence", 0)
                            frequency = field.get("frequency", 0)
                            bar_color = "🟢" if confidence >= 0.7 else "🟡" if confidence >= 0.5 else "🔴"
                            st.markdown(
                                f"{bar_color} **{field['label']}** — "
                                f"{confidence*100:.0f}% confidence ({frequency}/{count} documents)"
                            )

    # Tab 2: Indexed Documents
    with kb_tab2:
        st.markdown("### Indexed Documents by Type")

        if not doc_types:
            st.info("No documents indexed yet.")
        else:
            selected_type = st.selectbox(
                "Select document type to view:",
                options=[t["type"] for t in doc_types],
                key="kb_doc_type_select"
            )

            if selected_type:
                files = knowledge_db.get_scanned_files_by_type(selected_type, user_id=current_user.user_id)

                st.caption(f"Found {len(files)} documents")

                for file_info in files[:50]:  # Limit display to 50
                    file_name = os.path.basename(file_info["file_path"])
                    file_size_kb = file_info["file_size"] / 1024

                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        st.markdown(f"**{file_name}**")
                    with col_b:
                        st.caption(f"{file_size_kb:.1f} KB")
                    with col_c:
                        st.caption(file_info["scan_date"][:10])

    # Tab 3: Scanner Settings
    with kb_tab3:
        st.markdown("### Scanner Configuration")

        scanner = ScannerManager.get_instance(current_user.user_id)
        if scanner:
            status = scanner.get_status()

            st.markdown("#### Status")
            if status["is_running"]:
                st.success("✅ Scanner is running")

                if status.get("current_progress"):
                    prog = status["current_progress"]
                    st.progress(prog["current"] / max(prog["total"], 1))
                    st.caption(f"Processing: {prog['file']}")
                    st.caption(f"{prog['current']} / {prog['total']} files")
            else:
                st.warning("⚠️ Scanner is stopped")

            st.divider()

            st.markdown("#### Scan Paths")
            scan_paths = status.get("scan_paths", [])
            for path in scan_paths:
                exists = os.path.exists(path)
                icon = "✅" if exists else "❌"
                st.markdown(f"{icon} `{path}`")

            st.divider()
            st.markdown("#### Manual Controls")

            col_a, col_b = st.columns(2)

            with col_a:
                if st.button("Run Scan Now", type="primary", use_container_width=True):
                    with st.spinner("Running scan..."):
                        scanner.run_scan_once()
                    st.success("Scan completed")
                    st.rerun()

            with col_b:
                if st.button("Rebuild Templates", use_container_width=True):
                    with st.spinner("Rebuilding learned templates..."):
                        llm = get_llm()
                        collection = get_collection()
                        scanner_instance = DocumentScanner(
                            llm=llm,
                            chroma_collection=collection,
                            knowledge_db=knowledge_db,
                            user_id=current_user.user_id,
                        )
                        scanner_instance.build_learned_templates()
                        st.success("Templates rebuilt")
                        st.rerun()

            st.divider()

            st.markdown("#### Advanced Settings")

            new_interval = st.number_input(
                "Scan interval (minutes)",
                min_value=5,
                max_value=1440,
                value=status.get("scan_interval_minutes", 30),
                key="kb_scan_interval"
            )

            if st.button("Update Interval", key="update_scan_interval"):
                # This would require updating the scanner config
                st.info("Restart the scanner for the new interval to take effect")

        else:
            st.error("Background scanner not initialized")

    # Tab 4: Scan History
    with kb_tab4:
        st.markdown("### Recent Scan History")

        history = knowledge_db.get_scan_history(limit=20, user_id=current_user.user_id)

        if not history:
            st.info("No scan history yet.")
        else:
            for scan in history:
                status_icon = "✅" if scan["status"] == "completed" else "⏳"

                with st.expander(f"{status_icon} Scan on {scan['scan_start'][:10]}"):
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.metric("Scanned", scan["files_scanned"])
                    with col_b:
                        st.metric("Indexed", scan["files_indexed"])
                    with col_c:
                        st.metric("Failed", scan["files_failed"])

                    if scan["scan_end"]:
                        try:
                            import dateutil.parser
                            start = dateutil.parser.parse(scan["scan_start"])
                            end = dateutil.parser.parse(scan["scan_end"])
                            duration = (end - start).total_seconds()
                            st.caption(f"Duration: {duration:.0f} seconds")
                        except:
                            pass

                    if scan.get("errors"):
                        st.markdown("**Errors:**")
                        st.text(scan["errors"])


# ======================================================================
# Main Application
# ======================================================================

def main():
    """Main application entry point."""

    # Check authentication status
    if not require_auth(st.session_state):
        # Show verification, registration, or login page
        if st.session_state.get("verify_email"):
            render_verification_page(auth_manager)
        elif st.session_state.get("show_register", False):
            render_registration_page(auth_manager)
        else:
            render_login_page(auth_manager)
        return

    # User is authenticated
    current_user = st.session_state.current_user

    if current_user.must_change_password:
        st.warning("Password update required. You can continue, but update it from Settings -> Profile.")
        if st.button("Go to Password Settings", key="force_pw_change_cta"):
            st.session_state.show_settings = True
            st.rerun()

    # Auto-connect all users to the host's Ollama instance (no onboarding needed)
    # Only show onboarding wizard if explicitly using OpenAI with no key set
    if not st.session_state.get("onboarding_complete", False):
        if st.session_state.llm_provider == "ollama":
            # Ollama users connect directly to host — skip onboarding
            st.session_state.onboarding_complete = True
        elif st.session_state.llm_provider == "openai" and not st.session_state.openai_api_key:
            render_onboarding_wizard()
            return
        else:
            st.session_state.onboarding_complete = True

    # Render clean plain header
    st.title("Corporate Law Document Generator")
    st.caption("Document generation workspace")

    # Check LLM availability
    llm = get_llm()
    if not llm.is_available():
        if st.session_state.llm_provider == "ollama":
            st.markdown("""
            <div class="error-card">
                <strong>⚠️ Ollama Not Running</strong><br><br>
                The app is configured to use Ollama, but it's not running.<br><br>
                <strong>To fix this:</strong><br>
                1. Make sure Ollama is installed (<a href="https://ollama.com" target="_blank">ollama.com</a>)<br>
                2. Open a terminal and run: <code>ollama serve</code><br>
                3. Pull a model: <code>ollama pull llama3.1:8b</code><br>
                4. Refresh this page<br><br>
                <strong>Or:</strong> Click the gear icon in the sidebar to switch to OpenAI
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-card">
                <strong>⚠️ OpenAI API Key Required</strong><br><br>
                The app is configured to use OpenAI, but no valid API key was found.<br><br>
                <strong>To fix this:</strong><br>
                1. Go to <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a><br>
                2. Sign up or log in<br>
                3. Create a new API key<br>
                4. Click the gear icon in the sidebar → <strong>LLM Provider</strong><br>
                5. Enter your API key and click Save<br><br>
                <strong>Or:</strong> Install and use Ollama locally (free)
            </div>
            """, unsafe_allow_html=True)

    # Render sidebar with Settings access
    render_sidebar()

    # Check if settings page should be shown
    if st.session_state.get("show_settings"):
        render_settings_page()
        return

    # Check if knowledge base page should be shown
    if st.session_state.get("show_knowledge_base"):
        if current_user.is_admin():
            render_knowledge_base_page()
        else:
            st.error("Access denied. Knowledge Base management is admin-only.")
            st.session_state.show_knowledge_base = False
        return

    # Main workflow routing
    workflow_mode = st.session_state.get("workflow_mode")

    if workflow_mode == "edit":
        render_edit_workflow()
    elif workflow_mode == "create":
        render_create_workflow()
    elif workflow_mode == "learn":
        render_learn_workflow()
    else:
        render_landing_page()

    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
