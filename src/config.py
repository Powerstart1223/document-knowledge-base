import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Local model settings
    USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

    # ChromaDB settings
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./vectordb")
    COLLECTION_NAME = "documents"

    # Document processing settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    # Streamlit settings
    STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))

    # Upload settings
    UPLOAD_DIR = "./uploads"
    MAX_FILE_SIZE_MB = 50

    # Supported file types
    SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt"]

    # NetDocuments settings
    NETDOCUMENTS_CLIENT_ID = os.getenv("NETDOCUMENTS_CLIENT_ID")
    NETDOCUMENTS_CLIENT_SECRET = os.getenv("NETDOCUMENTS_CLIENT_SECRET")
    NETDOCUMENTS_REDIRECT_URI = os.getenv("NETDOCUMENTS_REDIRECT_URI", "https://localhost:3000/gettoken")
    NETDOCUMENTS_ENABLED = os.getenv("NETDOCUMENTS_ENABLED", "false").lower() == "true"

    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        if not cls.USE_LOCAL_MODEL and not cls.OPENAI_API_KEY:
            raise ValueError(
                "OpenAI API key is required when USE_LOCAL_MODEL=false. "
                "Set OPENAI_API_KEY in your .env file or set USE_LOCAL_MODEL=true"
            )

        # Create necessary directories
        os.makedirs(cls.CHROMA_DB_PATH, exist_ok=True)
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)

        # Validate NetDocuments configuration if enabled
        if cls.NETDOCUMENTS_ENABLED:
            if not cls.NETDOCUMENTS_CLIENT_ID or not cls.NETDOCUMENTS_CLIENT_SECRET:
                raise ValueError(
                    "NetDocuments integration enabled but client credentials missing. "
                    "Set NETDOCUMENTS_CLIENT_ID and NETDOCUMENTS_CLIENT_SECRET in your .env file"
                )