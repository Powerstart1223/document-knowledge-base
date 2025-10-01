import streamlit as st
import os
import tempfile
from typing import List
import sys

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from document_processor import DocumentProcessor
    from rag_pipeline import RAGPipeline
    from config import Config
    CORE_IMPORTS_SUCCESS = True
except ImportError as e:
    st.error(f"Core import error: {e}")
    CORE_IMPORTS_SUCCESS = False

# Optional imports - gracefully handle failures
try:
    from netdocuments_sync import NetDocumentsSync
    from netdocuments_integration import NetDocumentsAPI
    NETDOCS_AVAILABLE = True
except ImportError:
    NETDOCS_AVAILABLE = False

try:
    from document_drafter import DocumentDrafter
    from document_exporter import DocumentExporter
    DRAFTING_AVAILABLE = True
except ImportError:
    DRAFTING_AVAILABLE = False

# Configure Streamlit page
st.set_page_config(
    page_title="Document Knowledge Base",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "rag_pipeline" not in st.session_state:
    try:
        st.session_state.rag_pipeline = RAGPipeline()
        st.session_state.document_processor = DocumentProcessor()
        st.session_state.initialized = True
    except Exception as e:
        st.session_state.initialized = False
        st.session_state.init_error = str(e)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Initialize NetDocuments integration if enabled
if "netdocuments_sync" not in st.session_state and Config.NETDOCUMENTS_ENABLED:
    try:
        st.session_state.netdocuments_api = NetDocumentsAPI()
        st.session_state.netdocuments_sync = NetDocumentsSync(st.session_state.rag_pipeline)
        st.session_state.netdocuments_initialized = True
    except Exception as e:
        st.session_state.netdocuments_initialized = False
        st.session_state.netdocuments_error = str(e)

# Initialize document drafting
if "document_drafter" not in st.session_state:
    try:
        st.session_state.document_drafter = DocumentDrafter(st.session_state.rag_pipeline)
        st.session_state.document_exporter = DocumentExporter()
        st.session_state.drafting_initialized = True
    except Exception as e:
        st.session_state.drafting_initialized = False
        st.session_state.drafting_error = str(e)

def main():
    st.title("📚 Document Knowledge Base")
    st.markdown("Upload documents and ask questions about their content using AI")

    # Check if core imports succeeded
    if not CORE_IMPORTS_SUCCESS:
        st.error("❌ Core system components failed to load. Please check the deployment logs.")
        st.info("This usually means some required packages are missing. The deployment should retry automatically.")
        return

    # Check if system is properly initialized
    if not st.session_state.get("initialized", False):
        st.error("System initialization failed!")
        st.error(f"Error: {st.session_state.get('init_error', 'Unknown error')}")

        if "OPENAI_API_KEY" in st.session_state.get('init_error', ''):
            st.info("💡 **Setup Instructions:**")
            st.markdown("""
            1. Create a `.env` file in the project root
            2. Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`
            3. Or set `USE_LOCAL_MODEL=true` to use local embeddings (experimental)
            """)
        return

    # Sidebar for document management
    with st.sidebar:
        # Create tabs for different document sources
        tab1, tab2 = st.tabs(["📁 Local Files", "☁️ NetDocuments"])

        with tab1:
            st.header("📁 Local Document Upload")

            # File upload
            uploaded_files = st.file_uploader(
                "Upload Documents",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                help="Supported formats: PDF, DOCX, TXT"
            )

            if uploaded_files:
                if st.button("📤 Process Documents", type="primary"):
                    process_uploaded_files(uploaded_files)

        with tab2:
            render_netdocuments_tab()

        st.divider()

        # Knowledge base stats
        st.subheader("📊 Knowledge Base Stats")
        stats = st.session_state.rag_pipeline.get_knowledge_base_stats()

        if "error" not in stats:
            st.metric("Documents", stats.get("document_count", 0))
            st.text(f"Model: {stats.get('embedding_model', 'Unknown')}")
        else:
            st.error(stats["error"])

        # Clear knowledge base
        if st.button("🗑️ Clear Knowledge Base", type="secondary"):
            if st.confirm("Are you sure you want to clear all documents?"):
                result = st.session_state.rag_pipeline.clear_knowledge_base()
                if result["success"]:
                    st.success(result["message"])
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error(result["message"])

        st.divider()

        # Settings
        st.subheader("⚙️ Settings")
        retrieval_k = st.slider(
            "Documents to retrieve",
            min_value=1,
            max_value=10,
            value=5,
            help="Number of document chunks to retrieve for each query"
        )
        st.session_state.retrieval_k = retrieval_k

    # Main content area - create tabs for different functionalities
    main_tab1, main_tab2 = st.tabs(["💬 Q&A Chat", "✍️ Document Drafting"])

    with main_tab1:
        # Q&A Chat functionality
        col1, col2 = st.columns([2, 1])

        with col1:
            st.header("💬 Ask Questions")

            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

                    # Show sources for assistant messages
                    if message["role"] == "assistant" and "sources" in message:
                        if message["sources"]:
                            with st.expander("📖 Sources"):
                                for i, source in enumerate(message["sources"], 1):
                                    st.markdown(f"**{i}. {source['source']}** (Chunk {source['chunk_id']})")
                                    st.markdown(f"*Preview:* {source['content_preview']}")
                                    st.divider()

            # Chat input
            if prompt := st.chat_input("Ask a question about your documents..."):
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})

                with st.chat_message("user"):
                    st.markdown(prompt)

                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("Searching documents and generating answer..."):
                        response = st.session_state.rag_pipeline.query(
                            prompt,
                            k=st.session_state.get("retrieval_k", 5)
                        )

                    if response["success"]:
                        st.markdown(response["answer"])

                        # Store response with sources
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response["answer"],
                            "sources": response["sources"]
                        })

                        # Show sources
                        if response["sources"]:
                            with st.expander("📖 Sources"):
                                for i, source in enumerate(response["sources"], 1):
                                    st.markdown(f"**{i}. {source['source']}** (Chunk {source['chunk_id']})")
                                    st.markdown(f"*Preview:* {source['content_preview']}")
                                    st.divider()
                    else:
                        error_msg = f"Error: {response['answer']}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })

        with col2:
            st.header("🔍 Document Search")

            search_query = st.text_input("Search documents directly:")

            if search_query:
                search_results = st.session_state.rag_pipeline.search_documents(
                    search_query,
                    k=st.session_state.get("retrieval_k", 5)
                )

                if search_results:
                    st.subheader(f"Found {len(search_results)} relevant chunks:")

                    for i, result in enumerate(search_results, 1):
                        with st.expander(f"{i}. {result['source']} (Score: {result['similarity_score']:.3f})"):
                            st.markdown(result['content'])
                            st.caption(f"Chunk {result['chunk_id']} from {result['source']}")
                else:
                    st.info("No results found. Try uploading some documents first!")

    with main_tab2:
        # Document Drafting functionality
        render_document_drafting_tab()

def process_uploaded_files(uploaded_files: List):
    """Process uploaded files and add them to the knowledge base"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_files = len(uploaded_files)
    processed_documents = []

    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}...")

        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_file_path = tmp_file.name

            # Process document
            documents = st.session_state.document_processor.process_document(tmp_file_path)
            processed_documents.extend(documents)

            # Clean up temporary file
            os.unlink(tmp_file_path)

            progress_bar.progress((i + 1) / total_files)

        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            continue

    if processed_documents:
        status_text.text("Adding documents to knowledge base...")
        result = st.session_state.rag_pipeline.add_documents(processed_documents)

        if result["success"]:
            st.success(f"Successfully processed {len(uploaded_files)} files and added {result['document_count']} chunks to the knowledge base!")
            st.session_state.uploaded_files.extend([f.name for f in uploaded_files])
        else:
            st.error(f"Error adding documents to knowledge base: {result['message']}")

    progress_bar.empty()
    status_text.empty()

def render_netdocuments_tab():
    """Render the NetDocuments integration tab"""
    if not Config.NETDOCUMENTS_ENABLED:
        st.info("💡 NetDocuments integration is disabled")
        st.markdown("""
        To enable NetDocuments integration:
        1. Set `NETDOCUMENTS_ENABLED=true` in your .env file
        2. Add your NetDocuments credentials
        3. Restart the application
        """)
        return

    if not st.session_state.get("netdocuments_initialized", False):
        st.error("❌ NetDocuments initialization failed")
        error = st.session_state.get("netdocuments_error", "Unknown error")
        st.error(f"Error: {error}")
        return

    api = st.session_state.netdocuments_api
    sync_service = st.session_state.netdocuments_sync

    # Check connection status
    connection_status = api.get_connection_status()

    if not connection_status.get("connected", False):
        st.warning("🔐 NetDocuments Authentication Required")

        # Setup credentials if not configured
        if not api.config.get("client_id"):
            st.subheader("📋 Setup NetDocuments API")

            with st.form("netdocs_setup"):
                client_id = st.text_input("Client ID", help="From NetDocuments Developer Portal")
                client_secret = st.text_input("Client Secret", type="password")
                redirect_uri = st.text_input("Redirect URI", value="https://localhost:3000/gettoken")

                if st.form_submit_button("Save Credentials"):
                    if client_id and client_secret:
                        api.setup_credentials(client_id, client_secret, redirect_uri)
                        st.success("✅ Credentials saved!")
                        st.rerun()
                    else:
                        st.error("Please fill in all fields")

        else:
            # Show authorization link
            st.markdown("**Step 1:** Click the link below to authorize the application:")

            auth_url = api.get_authorization_url()
            st.markdown(f"[🔗 Authorize NetDocuments Access]({auth_url})")

            st.markdown("**Step 2:** Copy the authorization code from the redirect URL:")

            with st.form("auth_code_form"):
                auth_code = st.text_input("Authorization Code")
                if st.form_submit_button("Complete Authentication"):
                    if auth_code:
                        success = api.exchange_code_for_token(auth_code)
                        if success:
                            st.success("✅ Successfully authenticated!")
                            st.rerun()
                        else:
                            st.error("❌ Authentication failed. Please try again.")
                    else:
                        st.error("Please enter the authorization code")

    else:
        # Show connected user info
        st.success(f"✅ Connected as: {connection_status.get('user', 'Unknown')}")

        # Sync controls
        st.subheader("🔄 Document Sync")

        col1, col2 = st.columns(2)

        with col1:
            # Quick sync recent documents
            if st.button("📅 Sync Recent (30 days)", type="primary"):
                with st.spinner("Syncing recent documents..."):
                    result = sync_service.sync_recent_documents(days=30, max_results=20)

                if result["success"]:
                    st.success(f"✅ Synced {result['synced_count']} documents")
                else:
                    st.error(f"❌ Sync failed: {result.get('error', 'Unknown error')}")

                if result["failed_count"] > 0:
                    st.warning(f"⚠️ {result['failed_count']} documents failed to sync")

        with col2:
            # Search and sync specific documents
            if st.button("🔍 Search & Sync", type="secondary"):
                st.session_state.show_search_sync = True

        if st.session_state.get("show_search_sync", False):
            st.subheader("🔍 Search and Sync Documents")

            with st.form("search_sync_form"):
                search_query = st.text_input("Search Query", placeholder="e.g., contract, agreement, 2024")
                max_results = st.slider("Max Results", 5, 100, 20)

                if st.form_submit_button("Search and Sync"):
                    with st.spinner("Searching and syncing documents..."):
                        # Discover documents
                        documents = sync_service.discover_documents(search_query, max_results)

                        if documents:
                            # Sync discovered documents
                            result = sync_service.sync_documents(documents)

                            if result["success"]:
                                st.success(f"✅ Found and synced {result['synced_count']} documents")
                            else:
                                st.error(f"❌ Sync failed: {result.get('error', 'Unknown error')}")

                            if result["failed_count"] > 0:
                                st.warning(f"⚠️ {result['failed_count']} documents failed to sync")
                        else:
                            st.info("No documents found matching your query")

        # Sync statistics
        st.subheader("📊 Sync Statistics")
        stats = sync_service.get_sync_statistics()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Synced", stats.get("total_synced", 0))
        with col2:
            st.metric("Failed", stats.get("failed_documents", 0))
        with col3:
            last_sync = stats.get("last_sync")
            if last_sync:
                st.metric("Last Sync", last_sync.split("T")[0])  # Show date only
            else:
                st.metric("Last Sync", "Never")

def render_document_drafting_tab():
    """Render the document drafting interface"""

    if not st.session_state.get("drafting_initialized", False):
        st.error("❌ Document drafting initialization failed")
        error = st.session_state.get("drafting_error", "Unknown error")
        st.error(f"Error: {error}")

        if "OPENAI_API_KEY" in error:
            st.info("💡 Document drafting requires OpenAI API access (GPT-4)")
        return

    drafter = st.session_state.document_drafter
    exporter = st.session_state.document_exporter

    # Initialize session state for drafting
    if "drafted_document" not in st.session_state:
        st.session_state.drafted_document = ""
    if "document_metadata" not in st.session_state:
        st.session_state.document_metadata = {}

    st.header("✍️ AI Document Drafting")
    st.markdown("Generate professional documents based on learned styles from your knowledge base")

    # Style Learning Section
    with st.expander("📚 Style Learning", expanded=False):
        st.subheader("Learn Writing Styles")
        st.markdown("Analyze your uploaded documents to learn writing styles and formatting patterns")

        col1, col2 = st.columns([2, 1])

        with col1:
            if st.button("🧠 Learn Styles from Knowledge Base", type="primary"):
                with st.spinner("Analyzing documents and learning styles..."):
                    result = drafter.learn_styles_from_knowledge_base()

                if result["success"]:
                    st.success(result["message"])
                    st.json(result["learned_styles"])
                else:
                    st.error(result["message"])

        with col2:
            # Show available templates
            templates = drafter.get_available_templates()
            if templates["templates"]:
                st.metric("Learned Styles", templates["total_types"])
                for doc_type, info in templates["templates"].items():
                    st.text(f"{doc_type}: {info['sample_count']} samples")
            else:
                st.info("No styles learned yet")

    # Document Drafting Section
    st.subheader("📝 Create New Document")

    col1, col2 = st.columns([3, 1])

    with col1:
        # Document request input
        document_request = st.text_area(
            "Describe the document you want to create:",
            placeholder="e.g., Draft a contract for software licensing, Create a business proposal for AI consulting services, Write a technical specification for a web application",
            height=100
        )

        # Options
        col_a, col_b = st.columns(2)

        with col_a:
            # Document type selection
            available_types = list(drafter.learned_styles.keys()) if drafter.learned_styles else []
            if available_types:
                document_type = st.selectbox(
                    "Document Type (optional):",
                    ["Auto-detect"] + available_types
                )
                if document_type == "Auto-detect":
                    document_type = None
            else:
                document_type = st.selectbox(
                    "Document Type:",
                    ["general", "business", "legal", "technical"]
                )

        with col_b:
            use_knowledge_base = st.checkbox(
                "Use Knowledge Base Context",
                value=True,
                help="Include relevant information from your knowledge base in the document"
            )

    with col2:
        # Draft button
        if st.button("✍️ Draft Document", type="primary", disabled=not document_request.strip()):
            if document_request.strip():
                with st.spinner("Drafting document... This may take a moment"):
                    result = drafter.draft_document(
                        request=document_request,
                        document_type=document_type,
                        use_knowledge_base=use_knowledge_base
                    )

                if result["success"]:
                    st.session_state.drafted_document = result["document"]
                    st.session_state.document_metadata = result["metadata"]
                    st.success("✅ Document drafted successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {result['error']}")

    # Document Display and Edit Section
    if st.session_state.drafted_document:
        st.divider()
        st.subheader("📄 Generated Document")

        # Document editor
        edited_document = st.text_area(
            "Review and edit your document:",
            value=st.session_state.drafted_document,
            height=400,
            key="document_editor"
        )

        # Update the stored document if edited
        if edited_document != st.session_state.drafted_document:
            st.session_state.drafted_document = edited_document

        # Document actions
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Refinement
            if st.button("🔧 Refine"):
                st.session_state.show_refinement = True

        with col2:
            # Suggestions
            if st.button("💡 Get Suggestions"):
                suggestions = drafter.suggest_improvements(
                    st.session_state.drafted_document,
                    st.session_state.document_metadata.get("document_type", "general")
                )
                if suggestions:
                    st.info("💡 **Suggestions:**\n" + "\n".join(f"• {s}" for s in suggestions))
                else:
                    st.success("✅ Document looks good!")

        with col3:
            # Word count
            word_count = len(st.session_state.drafted_document.split())
            st.metric("Words", word_count)

        with col4:
            # Character count
            char_count = len(st.session_state.drafted_document)
            st.metric("Characters", char_count)

        # Refinement interface
        if st.session_state.get("show_refinement", False):
            st.subheader("🔧 Refine Document")

            refinement_request = st.text_area(
                "What would you like to change or improve?",
                placeholder="e.g., Make it more formal, Add more technical details, Shorten the introduction",
                height=80
            )

            col_r1, col_r2 = st.columns([1, 3])

            with col_r1:
                if st.button("Apply Refinement", type="primary"):
                    if refinement_request.strip():
                        with st.spinner("Refining document..."):
                            result = drafter.refine_document(
                                st.session_state.drafted_document,
                                refinement_request
                            )

                        if result["success"]:
                            st.session_state.drafted_document = result["refined_document"]
                            st.success("✅ Document refined!")
                            st.session_state.show_refinement = False
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {result['error']}")

            with col_r2:
                if st.button("Cancel"):
                    st.session_state.show_refinement = False
                    st.rerun()

        # Export Section
        st.divider()
        st.subheader("📥 Export Document")

        # Export format selection
        export_formats = exporter.get_supported_formats()
        available_formats = [fmt for fmt, info in export_formats["supported_formats"].items() if info["available"]]

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            export_format = st.selectbox(
                "Export Format:",
                available_formats,
                format_func=lambda x: f"{x.upper()} - {export_formats['supported_formats'][x]['description']}"
            )

        with col2:
            export_filename = st.text_input(
                "Filename (optional):",
                placeholder=f"my_document.{export_format}"
            )

        with col3:
            if st.button("📥 Export", type="primary"):
                with st.spinner(f"Exporting to {export_format.upper()}..."):
                    result = exporter.export_document(
                        content=st.session_state.drafted_document,
                        format_type=export_format,
                        filename=export_filename if export_filename else None,
                        document_type=st.session_state.document_metadata.get("document_type", "general")
                    )

                if result["success"]:
                    st.success(f"✅ Document exported as {result['filename']}")

                    # Provide download link
                    with open(result["file_path"], "rb") as file:
                        st.download_button(
                            label=f"📥 Download {result['filename']}",
                            data=file.read(),
                            file_name=result["filename"],
                            mime=f"application/{export_format}"
                        )
                else:
                    st.error(f"❌ Export failed: {result['error']}")

        # Show unavailable formats
        unavailable_formats = [fmt for fmt, info in export_formats["supported_formats"].items() if not info["available"]]
        if unavailable_formats:
            st.info("ℹ️ Additional formats available with: " +
                   ", ".join(f"`pip install {export_formats['supported_formats'][fmt]['requirements']}`"
                            for fmt in unavailable_formats if export_formats['supported_formats'][fmt].get('requirements')))

if __name__ == "__main__":
    main()