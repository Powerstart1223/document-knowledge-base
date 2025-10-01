import streamlit as st
import os
from typing import List

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

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "document_texts" not in st.session_state:
    st.session_state.document_texts = []

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
        if uploaded_file.type == "text/plain":
            return str(uploaded_file.read(), "utf-8")
        else:
            return "Only text files are supported in this simplified version. Please upload a .txt file."
    except Exception as e:
        return f"Error reading file: {str(e)}"

def simple_qa_with_openai(question: str, context: str):
    """Simple Q&A using OpenAI API directly"""
    try:
        if not st.session_state.get("openai_configured", False):
            return "❌ OpenAI API key not configured. Please add OPENAI_API_KEY in Streamlit Cloud secrets."

        prompt = f"""Answer the question based on the provided context. If the context doesn't contain enough information to answer the question, say so clearly.

Context from uploaded documents:
{context}

Question: {question}

Please provide a helpful answer based on the context above:"""

        # Use OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Error generating answer: {str(e)}"

def main():
    st.title("📚 Document Knowledge Base")
    st.markdown("**Simplified Version** - Upload text documents and ask questions using AI")

    # Sidebar for document management
    with st.sidebar:
        st.header("📁 Document Upload")

        # File upload
        uploaded_files = st.file_uploader(
            "Upload Text Documents",
            type=["txt"],
            accept_multiple_files=True,
            help="Upload .txt files to get started"
        )

        if uploaded_files:
            if st.button("📤 Process Documents", type="primary"):
                process_uploaded_files(uploaded_files)

        st.divider()

        # Simple stats
        st.subheader("📊 Status")
        st.metric("Documents Loaded", len(st.session_state.document_texts))

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
        1. **Upload** .txt files using the uploader above
        2. **Process** them by clicking the button
        3. **Ask questions** in the chat below
        4. **Get AI answers** based on your documents
        """)

    # Main content area
    st.header("💬 Ask Questions About Your Documents")

    # Show help if no documents
    if not st.session_state.document_texts:
        st.info("👋 Welcome! Upload some text documents in the sidebar to get started.")
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
            with st.spinner("Generating answer..."):
                # Combine all document texts as context
                context = "\n\n---\n\n".join(st.session_state.document_texts)

                # Limit context size to avoid token limits
                if len(context) > 8000:  # Rough character limit
                    context = context[:8000] + "\n\n[Content truncated...]"

                response = simple_qa_with_openai(prompt, context)

            st.markdown(response)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

def process_uploaded_files(uploaded_files: List):
    """Process uploaded files and store them"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    new_texts = []
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}...")

        try:
            text = extract_text_from_file(uploaded_file)
            new_texts.append(f"=== {uploaded_file.name} ===\n\n{text}")
            progress_bar.progress((i + 1) / len(uploaded_files))
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")

    if new_texts:
        st.session_state.document_texts.extend(new_texts)
        st.success(f"✅ Successfully processed {len(new_texts)} files!")

    progress_bar.empty()
    status_text.empty()

if __name__ == "__main__":
    main()