"""
Corporate Law Document Generator — Streamlit Application v2.0

MAJOR UPDATE: Multi-user authentication system with modern UX

Features:
- User authentication (login/registration)
- Per-user data isolation
- Role-based access (admin/user)
- Modern, professional UI
- Three-tab interface: Chat Q&A, Generate Document, Settings
- Admin panel for user management
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from typing import List
from datetime import date

import chromadb
from chromadb.utils import embedding_functions

from llm_backend import LLMBackend
from document_generator import DocumentGenerator, DOCUMENT_TYPES
from api_clients import SECEdgarClient, LegalDatabaseClient

# Authentication imports
from auth import AuthManager, init_session_state, require_auth, get_user_collection_name
from auth_ui import (
    render_login_page,
    render_registration_page,
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
    """Auto-detect best LLM provider based on environment."""
    try:
        if "LLM_PROVIDER" in st.secrets:
            return st.secrets.get("LLM_PROVIDER", "openai")
    except Exception:
        pass

    provider = os.getenv("LLM_PROVIDER", "").lower()
    if provider in ["ollama", "openai"]:
        return provider

    if is_streamlit_cloud():
        return "openai"

    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            return "ollama"
    except Exception:
        pass

    return "openai"


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
    "legal_db_api_key": get_config_value("LEGAL_DB_API_KEY", ""),
    "generated_text": "",
    "generated_title": "",
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


def get_legal_db_client() -> LegalDatabaseClient:
    return LegalDatabaseClient(api_key=st.session_state.legal_db_api_key)


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
        file_key = f"{st.session_state.current_user.user_id}_{filename}"

        if file_key in st.session_state.processed_files:
            progress.progress((i + 1) / len(uploaded_files))
            continue

        status.text(f"Processing {filename}...")
        try:
            text = extract_text_from_file(f)
            chunks = chunk_text(text)
            if chunks:
                ids = [f"{file_key}_chunk_{j}" for j in range(len(chunks))]
                metadatas = [
                    {
                        "source": filename,
                        "chunk_index": j,
                        "document_type": document_type,
                        "user_id": st.session_state.current_user.user_id,
                    }
                    for j in range(len(chunks))
                ]
                collection.add(documents=chunks, ids=ids, metadatas=metadatas)
                total_chunks += len(chunks)
                new_files += 1
                st.session_state.processed_files.add(file_key)
            progress.progress((i + 1) / len(uploaded_files))
        except Exception as e:
            st.error(f"Error processing {filename}: {e}")

    if new_files:
        st.toast(f"✅ Processed {new_files} file(s) into {total_chunks} chunks.", icon="✅")
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
    """Render the sidebar with user info and document upload."""
    current_user = st.session_state.current_user

    # Auth sidebar section
    render_auth_sidebar(current_user)

    # Document upload section
    st.markdown("""
    <div class="card-header">
        📄 Document Upload
    </div>
    """, unsafe_allow_html=True)

    doc_type_options = list(DOCUMENT_TYPES.keys()) + ["reference"]
    selected_type = st.selectbox(
        "Document type tag",
        options=doc_type_options,
        format_func=lambda k: (
            DOCUMENT_TYPES[k]["label"] if k in DOCUMENT_TYPES else "Reference / Other"
        ),
        help="Tag uploaded files so the generator can retrieve matching style examples.",
    )

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True,
        key="file_uploader"
    )

    if uploaded_files:
        if st.button("Process Documents", type="primary", use_container_width=True):
            with st.spinner("Processing documents..."):
                process_uploaded_files(uploaded_files, selected_type)

    st.divider()

    # Database stats
    st.markdown("""
    <div class="card-header">
        📊 Database Stats
    </div>
    """, unsafe_allow_html=True)

    stats = get_db_stats()
    st.metric("Total Chunks", stats["total"])

    if stats["total"] > 0:
        for dtype in list(DOCUMENT_TYPES.keys()) + ["reference"]:
            count = stats.get(dtype, 0)
            if count > 0:
                label = (
                    DOCUMENT_TYPES[dtype]["label"]
                    if dtype in DOCUMENT_TYPES
                    else "Reference"
                )
                st.caption(f"  {label}: {count}")

    collection = get_collection()
    if collection.count() > 0:
        if st.button("🗑️ Clear My Database", use_container_width=True):
            if st.button("⚠️ Confirm Delete", type="secondary", use_container_width=True):
                client = get_chroma_client()
                collection_name = get_user_collection_name(current_user.user_id)
                try:
                    client.delete_collection(collection_name)
                    st.session_state.processed_files = set()
                    st.session_state.messages = []
                    st.success("Database cleared successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing database: {e}")

    st.divider()

    # Connection status
    st.markdown("""
    <div class="card-header">
        🔌 Connections
    </div>
    """, unsafe_allow_html=True)

    llm = get_llm()
    if llm.is_available():
        provider_label = st.session_state.llm_provider.title()
        st.markdown(f"""
        <div class="status-badge status-success">
            <span class="connection-indicator connection-success"></span>
            LLM: {provider_label} ({st.session_state.llm_model})
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-badge status-error">
            <span class="connection-indicator connection-error"></span>
            LLM: Not connected
        </div>
        """, unsafe_allow_html=True)

    sec = get_sec_client()
    if sec.is_configured():
        st.markdown("""
        <div class="status-badge status-success">
            SEC EDGAR: Configured
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-badge status-warning">
            SEC EDGAR: Not configured
        </div>
        """, unsafe_allow_html=True)



# ======================================================================
# TAB 1 — Chat Q&A
# ======================================================================

def render_chat_tab():
    """Render the chat Q&A interface."""
    st.markdown("""
    <div class="card-header">
        💬 Chat Q&A - Ask Questions About Your Documents
    </div>
    """, unsafe_allow_html=True)

    st.caption("Ask questions about your uploaded documents. Answers are generated by the configured LLM with RAG.")

    collection = get_collection()
    if collection.count() == 0:
        st.markdown("""
        <div class="info-card">
            📄 <strong>No documents yet!</strong><br>
            Upload and process documents in the sidebar to start chatting.
        </div>
        """, unsafe_allow_html=True)
        return

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
# TAB 2 — Generate Document
# ======================================================================

def render_generate_tab():
    """Render the document generation interface."""
    st.markdown("""
    <div class="card-header">
        📝 Generate Document - Create Professional Legal Drafts
    </div>
    """, unsafe_allow_html=True)

    st.caption(
        "Select a document type, fill in the parameters, and generate a professional draft. "
        "All generated documents are drafts for attorney review."
    )

    # Check LLM availability
    llm = get_llm()
    if not llm.is_available():
        st.markdown("""
        <div class="warning-card">
            ⚠️ <strong>LLM Not Configured</strong><br>
            Please configure your LLM provider in the Settings tab before generating documents.
        </div>
        """, unsafe_allow_html=True)
        return

    # Document type selector
    doc_type = st.selectbox(
        "Document type",
        options=list(DOCUMENT_TYPES.keys()),
        format_func=lambda k: DOCUMENT_TYPES[k]["label"],
        key="gen_doc_type",
    )

    doc_def = DOCUMENT_TYPES[doc_type]
    st.markdown(f"*{doc_def['description']}*")

    st.divider()

    # Dynamic form
    params = {}
    with st.form("doc_gen_form"):
        st.markdown("### Document Parameters")

        for field in doc_def["fields"]:
            key = field["key"]
            label = field["label"]
            ftype = field.get("type", "text")
            placeholder = field.get("placeholder", "")

            if ftype == "date":
                params[key] = st.date_input(label, value=date.today(), key=f"gen_{key}")
            elif ftype == "textarea":
                params[key] = st.text_area(
                    label, placeholder=placeholder, key=f"gen_{key}", height=120
                )
            else:
                params[key] = st.text_input(
                    label, placeholder=placeholder, key=f"gen_{key}"
                )

        st.divider()
        st.markdown("### Optional Data Sources")

        use_sec = st.checkbox(
            "📊 Pull SEC EDGAR data",
            help="Fetch relevant SEC filings for context",
        )

        st.divider()
        submitted = st.form_submit_button("✨ Generate Document", type="primary", use_container_width=True)

    if submitted:
        llm = get_llm()
        if not llm.is_available():
            st.error(
                "LLM is not available. Check that Ollama is running or OpenAI key is set in Settings."
            )
            return

        collection = get_collection()
        generator = DocumentGenerator(llm, collection)
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
                return

    # Preview & download
    if st.session_state.generated_text:
        st.divider()
        st.markdown("""
        <div class="card-header">
            📄 Preview & Download
        </div>
        """, unsafe_allow_html=True)

        st.text_area(
            "Generated document",
            value=st.session_state.generated_text,
            height=500,
            key="gen_preview",
        )

        col1, col2 = st.columns([3, 1])
        with col2:
            docx_bytes = DocumentGenerator.text_to_docx(
                st.session_state.generated_text,
                st.session_state.generated_title,
            )
            safe_name = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_"
                for c in st.session_state.generated_title
            ).strip()
            st.download_button(
                label="⬇️ Download as .docx",
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
            🤖 LLM Provider Configuration
        </div>
        """, unsafe_allow_html=True)

        provider = st.radio(
            "Provider",
            options=["ollama", "openai"],
            format_func=lambda p: "Ollama (local only)" if p == "ollama" else "OpenAI (cloud-compatible)",
            index=0 if st.session_state.llm_provider == "ollama" else 1,
            key="settings_provider",
            horizontal=True,
        )

        if provider == "ollama" and is_streamlit_cloud():
            st.markdown("""
            <div class="warning-card">
                ⚠️ <strong>Ollama Not Available on Cloud</strong><br>
                Ollama is not available on Streamlit Cloud. Please use OpenAI provider instead.
            </div>
            """, unsafe_allow_html=True)

        if provider == "ollama":
            base_url = st.text_input(
                "Ollama base URL",
                value=st.session_state.llm_base_url,
                key="settings_base_url",
            )
            tmp_llm = LLMBackend(provider="ollama", base_url=base_url)
            models = tmp_llm.list_models()
            if models:
                model = st.selectbox(
                    "Model",
                    options=models,
                    index=models.index(st.session_state.llm_model)
                    if st.session_state.llm_model in models
                    else 0,
                    key="settings_model_select",
                )
            else:
                model = st.text_input(
                    "Model name",
                    value=st.session_state.llm_model,
                    key="settings_model_text",
                )
                st.warning("Could not connect to Ollama to list models.")
        else:
            st.markdown(
                "Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)"
            )
            api_key = st.text_input(
                "OpenAI API Key",
                value=st.session_state.openai_api_key if st.session_state.openai_api_key != "your-api-key-here" else "",
                type="password",
                key="settings_openai_key",
                help="Your OpenAI API key (starts with sk-)",
            )
            model_options = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
            current_model = st.session_state.llm_model if st.session_state.llm_provider == "openai" else "gpt-4o-mini"
            model = st.selectbox(
                "Model",
                options=model_options,
                index=model_options.index(current_model) if current_model in model_options else 0,
                key="settings_openai_model",
                help="gpt-4o-mini is recommended for cost-effectiveness",
            )
            base_url = "https://api.openai.com/v1"

            if api_key:
                if api_key.startswith("sk-") and len(api_key) > 20:
                    st.markdown("""
                    <div class="success-card">
                        ✅ API key format looks valid
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="warning-card">
                        ⚠️ API key format may be invalid (should start with 'sk-')
                    </div>
                    """, unsafe_allow_html=True)

        if st.button("💾 Save LLM Settings", type="primary"):
            st.session_state.llm_provider = provider
            st.session_state.llm_model = model
            st.session_state.llm_base_url = base_url
            if provider == "openai":
                st.session_state.openai_api_key = api_key
            st.toast("✅ LLM settings saved!", icon="✅")
            st.success("LLM settings saved.")

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

        # OpenAI API Key (quick access)
        st.subheader("🔑 OpenAI API Key")
        st.caption("Required when using OpenAI as LLM provider. Get your key from [OpenAI Platform](https://platform.openai.com/api-keys).")
        openai_key = st.text_input(
            "API Key",
            value=st.session_state.openai_api_key if st.session_state.openai_api_key not in ["", "your-api-key-here"] else "",
            type="password",
            key="settings_integrations_openai_key",
            placeholder="sk-proj-...",
        )
        if st.button("💾 Save OpenAI Key", key="save_openai_key_integrations"):
            st.session_state.openai_api_key = openai_key
            if st.session_state.llm_provider == "openai":
                st.toast("✅ OpenAI API key saved and active!", icon="✅")
                st.success("OpenAI API key saved. It's now active since your provider is set to OpenAI.")
            else:
                st.toast("✅ OpenAI API key saved!", icon="✅")
                st.success("OpenAI API key saved. Switch to OpenAI provider in LLM settings to use it.")

        st.divider()

        # SEC EDGAR
        st.subheader("📊 SEC EDGAR")
        sec_ua = st.text_input(
            "User-Agent (name + email)",
            value=st.session_state.sec_user_agent,
            placeholder="YourName your@email.com",
            help="SEC EDGAR requires a User-Agent header with a contact name and email.",
            key="settings_sec_ua",
        )
        if st.button("💾 Save SEC EDGAR Settings"):
            st.session_state.sec_user_agent = sec_ua
            st.toast("✅ SEC EDGAR settings saved!", icon="✅")
            st.success("SEC EDGAR settings saved.")

        st.divider()

        # Westlaw / LexisNexis
        st.subheader("⚖️ Westlaw / LexisNexis (Stub)")
        st.caption(
            "These services require commercial API subscriptions. "
            "Enter your API key when available."
        )
        legal_key = st.text_input(
            "API Key",
            value=st.session_state.legal_db_api_key,
            type="password",
            key="settings_legal_key",
        )
        if st.button("💾 Save Legal DB Key"):
            st.session_state.legal_db_api_key = legal_key
            st.toast("✅ Legal database API key saved!", icon="✅")
            st.success("Legal database API key saved.")

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
# Main Application
# ======================================================================

def main():
    """Main application entry point."""

    # Check authentication status
    if not require_auth(st.session_state):
        # Show login or registration page
        if st.session_state.get("show_register", False):
            render_registration_page(auth_manager)
        else:
            render_login_page(auth_manager)
        return

    # User is authenticated - show main app
    current_user = st.session_state.current_user

    # Render header
    subtitle_provider = st.session_state.llm_provider.title()
    render_header(
        title="Corporate Law Document Generator",
        subtitle=f"RAG-powered document generation with AI-assisted legal drafting • {subtitle_provider}",
        user_info=current_user.to_dict()
    )

    # Check LLM availability and show warning if not configured
    llm = get_llm()
    if not llm.is_available():
        if st.session_state.llm_provider == "ollama":
            st.markdown("""
            <div class="error-card">
                ❌ <strong>Ollama Not Running</strong><br>
                Ollama is not running or not available. Please start Ollama locally or switch to OpenAI in Settings.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-card">
                ❌ <strong>OpenAI API Key Missing</strong><br>
                OpenAI API key is missing or invalid. Please add your API key in the Settings tab.
                Get your key from <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a>
            </div>
            """, unsafe_allow_html=True)

    # Render sidebar
    render_sidebar()

    # Main content tabs
    tab_chat, tab_generate, tab_settings = st.tabs([
        "💬 Chat Q&A",
        "📝 Generate Document",
        "⚙️ Settings"
    ])

    with tab_chat:
        render_chat_tab()

    with tab_generate:
        render_generate_tab()

    with tab_settings:
        render_settings_tab()

    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
