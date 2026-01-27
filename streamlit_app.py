"""
Corporate Law Document Generator — Streamlit Application

Three-tab UI:
  Tab 1 — Chat Q&A (RAG over uploaded documents, powered by Ollama/OpenAI)
  Tab 2 — Generate Document (contract, memo, brief, filing)
  Tab 3 — Settings (LLM provider, SEC EDGAR, NetDocuments, Westlaw/Lexis)

Sidebar: file upload with document-type tagging, database stats, connection status.
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
from api_clients import SECEdgarClient, NetDocumentsClient, LegalDatabaseClient

# ======================================================================
# Page config
# ======================================================================
st.set_page_config(
    page_title="Corporate Law Document Generator",
    page_icon=":material/gavel:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================================================================
# Session state defaults
# ======================================================================
_DEFAULTS = {
    "messages": [],
    "processed_files": set(),
    # LLM settings
    "llm_provider": os.getenv("LLM_PROVIDER", "ollama"),
    "llm_model": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
    "llm_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    # SEC EDGAR
    "sec_user_agent": os.getenv("SEC_EDGAR_USER_AGENT", ""),
    # NetDocuments
    "nd_client_id": os.getenv("NETDOCUMENTS_CLIENT_ID", ""),
    "nd_client_secret": os.getenv("NETDOCUMENTS_CLIENT_SECRET", ""),
    "nd_redirect_uri": os.getenv("NETDOCUMENTS_REDIRECT_URI", "https://localhost:3000/gettoken"),
    "nd_access_token": None,
    # Westlaw / LexisNexis
    "legal_db_api_key": os.getenv("LEGAL_DB_API_KEY", ""),
    # Generated document state
    "generated_text": "",
    "generated_title": "",
}
for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ======================================================================
# ChromaDB setup
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
    client = get_chroma_client()
    ef = get_embedding_function()
    return client.get_or_create_collection(name="documents", embedding_function=ef)


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


def get_netdocs_client() -> NetDocumentsClient:
    client = NetDocumentsClient(
        client_id=st.session_state.nd_client_id,
        client_secret=st.session_state.nd_client_secret,
        redirect_uri=st.session_state.nd_redirect_uri,
    )
    if st.session_state.nd_access_token:
        client.access_token = st.session_state.nd_access_token
    return client


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
        if filename in st.session_state.processed_files:
            progress.progress((i + 1) / len(uploaded_files))
            continue

        status.text(f"Processing {filename}...")
        try:
            text = extract_text_from_file(f)
            chunks = chunk_text(text)
            if chunks:
                ids = [f"{filename}_chunk_{j}" for j in range(len(chunks))]
                metadatas = [
                    {
                        "source": filename,
                        "chunk_index": j,
                        "document_type": document_type,
                    }
                    for j in range(len(chunks))
                ]
                collection.add(documents=chunks, ids=ids, metadatas=metadatas)
                total_chunks += len(chunks)
                new_files += 1
                st.session_state.processed_files.add(filename)
            progress.progress((i + 1) / len(uploaded_files))
        except Exception as e:
            st.error(f"Error processing {filename}: {e}")

    if new_files:
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
            result = collection.get(where={"document_type": dtype}, limit=1, include=[])
            # ChromaDB .get() doesn't return a count directly, so query instead
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
    with st.sidebar:
        st.header("Document Upload")

        doc_type_options = list(DOCUMENT_TYPES.keys()) + ["reference"]
        doc_type_labels = [
            DOCUMENT_TYPES[k]["label"] if k in DOCUMENT_TYPES else "Reference / Other"
            for k in doc_type_options
        ]
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
        )

        if uploaded_files:
            if st.button("Process Documents", type="primary"):
                process_uploaded_files(uploaded_files, selected_type)

        st.divider()

        # Stats
        st.subheader("Database Stats")
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
            if st.button("Clear Database"):
                client = get_chroma_client()
                client.delete_collection("documents")
                st.session_state.processed_files = set()
                st.session_state.messages = []
                st.rerun()

        st.divider()

        # Connection status
        st.subheader("Connections")
        llm = get_llm()
        if llm.is_available():
            provider_label = st.session_state.llm_provider.title()
            st.success(f"LLM: {provider_label} ({st.session_state.llm_model})")
        else:
            st.error("LLM: Not connected")

        sec = get_sec_client()
        if sec.is_configured():
            st.success("SEC EDGAR: Configured")
        else:
            st.warning("SEC EDGAR: Not configured")

        nd = get_netdocs_client()
        if nd.is_configured():
            if nd.is_authenticated():
                st.success("NetDocuments: Connected")
            else:
                st.warning("NetDocuments: Configured (not authenticated)")
        else:
            st.caption("NetDocuments: Not configured")

        legal = get_legal_db_client()
        if legal.is_configured():
            st.success("Westlaw/Lexis: Configured")
        else:
            st.caption("Westlaw/Lexis: Not configured (stub)")


# ======================================================================
# TAB 1 — Chat Q&A
# ======================================================================

def render_chat_tab():
    st.header("Chat Q&A")
    st.caption("Ask questions about your uploaded documents. Answers are generated by the configured LLM with RAG.")

    collection = get_collection()
    if collection.count() == 0:
        st.info("Upload and process documents in the sidebar to start chatting.")
        return

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching documents and generating answer..."):
                response, sources = rag_query(prompt)
            st.markdown(response)
            if sources:
                st.caption(f"Sources: {', '.join(sources)}")
            full = response
            if sources:
                full += f"\n\n*Sources: {', '.join(sources)}*"
            st.session_state.messages.append({"role": "assistant", "content": full})


# ======================================================================
# TAB 2 — Generate Document
# ======================================================================

def render_generate_tab():
    st.header("Generate Document")
    st.caption(
        "Select a document type, fill in the parameters, and generate a professional draft. "
        "All generated documents are drafts for attorney review."
    )

    # Document type selector
    doc_type = st.selectbox(
        "Document type",
        options=list(DOCUMENT_TYPES.keys()),
        format_func=lambda k: DOCUMENT_TYPES[k]["label"],
        key="gen_doc_type",
    )

    doc_def = DOCUMENT_TYPES[doc_type]
    st.markdown(f"*{doc_def['description']}*")

    # Dynamic form
    params = {}
    with st.form("doc_gen_form"):
        for field in doc_def["fields"]:
            key = field["key"]
            label = field["label"]
            ftype = field.get("type", "text")
            placeholder = field.get("placeholder", "")

            if ftype == "date":
                params[key] = st.date_input(label, value=date.today(), key=f"gen_{key}")
            elif ftype == "textarea":
                params[key] = st.text_area(
                    label, placeholder=placeholder, key=f"gen_{key}"
                )
            else:
                params[key] = st.text_input(
                    label, placeholder=placeholder, key=f"gen_{key}"
                )

        # Optional data sources
        col1, col2 = st.columns(2)
        with col1:
            use_sec = st.checkbox(
                "Pull SEC EDGAR data",
                help="Fetch relevant SEC filings for context",
            )
        with col2:
            use_netdocs = st.checkbox(
                "Search NetDocuments",
                help="Pull related documents from NetDocuments (requires auth)",
            )

        submitted = st.form_submit_button("Generate Document", type="primary")

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
        nd_client = get_netdocs_client() if use_netdocs else None

        with st.spinner("Generating document... this may take a moment."):
            try:
                text = generator.generate(
                    doc_type,
                    params,
                    sec_client=sec_client,
                    netdocs_client=nd_client,
                    use_sec=use_sec,
                    use_netdocs=use_netdocs,
                )
                st.session_state.generated_text = text
                st.session_state.generated_title = (
                    f"{doc_def['label']} — {params.get('party_a', '') or params.get('entity_name', '') or params.get('case_caption', '') or params.get('re', '') or 'Draft'}"
                )
            except Exception as e:
                st.error(f"Generation failed: {e}")
                return

    # Preview & download
    if st.session_state.generated_text:
        st.subheader("Preview")
        st.text_area(
            "Generated document",
            value=st.session_state.generated_text,
            height=500,
            key="gen_preview",
        )

        docx_bytes = DocumentGenerator.text_to_docx(
            st.session_state.generated_text,
            st.session_state.generated_title,
        )
        safe_name = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_"
            for c in st.session_state.generated_title
        ).strip()
        st.download_button(
            label="Download as .docx",
            data=docx_bytes,
            file_name=f"{safe_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


# ======================================================================
# TAB 3 — Settings
# ======================================================================

def render_settings_tab():
    st.header("Settings")

    # -- LLM Provider ---------------------------------------------------
    st.subheader("LLM Provider")

    provider = st.radio(
        "Provider",
        options=["ollama", "openai"],
        format_func=lambda p: "Ollama (local)" if p == "ollama" else "OpenAI (cloud)",
        index=0 if st.session_state.llm_provider == "ollama" else 1,
        key="settings_provider",
        horizontal=True,
    )

    if provider == "ollama":
        base_url = st.text_input(
            "Ollama base URL",
            value=st.session_state.llm_base_url,
            key="settings_base_url",
        )
        # Try to list models
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
        api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.openai_api_key,
            type="password",
            key="settings_openai_key",
        )
        model = st.text_input(
            "Model name",
            value="gpt-4" if st.session_state.llm_provider != "openai" else st.session_state.llm_model,
            key="settings_openai_model",
        )
        base_url = "https://api.openai.com/v1"

    if st.button("Save LLM Settings"):
        st.session_state.llm_provider = provider
        st.session_state.llm_model = model
        st.session_state.llm_base_url = base_url
        if provider == "openai":
            st.session_state.openai_api_key = api_key
        st.success("LLM settings saved.")

    st.divider()

    # -- SEC EDGAR ------------------------------------------------------
    st.subheader("SEC EDGAR")
    sec_ua = st.text_input(
        "User-Agent (name + email)",
        value=st.session_state.sec_user_agent,
        placeholder="YourName your@email.com",
        help="SEC EDGAR requires a User-Agent header with a contact name and email.",
        key="settings_sec_ua",
    )
    if st.button("Save SEC EDGAR Settings"):
        st.session_state.sec_user_agent = sec_ua
        st.success("SEC EDGAR settings saved.")

    st.divider()

    # -- NetDocuments ---------------------------------------------------
    st.subheader("NetDocuments")
    nd_id = st.text_input(
        "Client ID",
        value=st.session_state.nd_client_id,
        key="settings_nd_id",
    )
    nd_secret = st.text_input(
        "Client Secret",
        value=st.session_state.nd_client_secret,
        type="password",
        key="settings_nd_secret",
    )
    nd_redirect = st.text_input(
        "Redirect URI",
        value=st.session_state.nd_redirect_uri,
        key="settings_nd_redirect",
    )

    if st.button("Save NetDocuments Credentials"):
        st.session_state.nd_client_id = nd_id
        st.session_state.nd_client_secret = nd_secret
        st.session_state.nd_redirect_uri = nd_redirect
        st.success("NetDocuments credentials saved.")

    # OAuth flow
    if nd_id and nd_secret:
        nd_client = NetDocumentsClient(nd_id, nd_secret, nd_redirect)
        auth_url = nd_client.get_authorization_url()
        st.markdown(f"[Authorize with NetDocuments]({auth_url})")

        auth_code = st.text_input(
            "Paste authorization code here",
            key="settings_nd_auth_code",
        )
        if auth_code and st.button("Authenticate"):
            try:
                nd_client.authenticate(auth_code)
                st.session_state.nd_access_token = nd_client.access_token
                st.success("NetDocuments authenticated successfully.")
            except Exception as e:
                st.error(f"Authentication failed: {e}")

    st.divider()

    # -- Westlaw / LexisNexis -------------------------------------------
    st.subheader("Westlaw / LexisNexis (Stub)")
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
    if st.button("Save Legal DB Key"):
        st.session_state.legal_db_api_key = legal_key
        st.success("Legal database API key saved.")


# ======================================================================
# Main
# ======================================================================

def main():
    st.title("Corporate Law Document Generator")
    st.caption("RAG-powered document generation with local Llama via Ollama")

    render_sidebar()

    tab_chat, tab_generate, tab_settings = st.tabs(
        ["Chat Q&A", "Generate Document", "Settings"]
    )

    with tab_chat:
        render_chat_tab()

    with tab_generate:
        render_generate_tab()

    with tab_settings:
        render_settings_tab()


if __name__ == "__main__":
    main()
