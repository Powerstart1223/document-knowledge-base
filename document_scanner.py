"""
Document Scanner — Discovers and indexes legal documents from local storage.

Recursively scans directories for legal documents (.pdf, .docx, .txt, .doc),
extracts text, classifies document types using LLM, and stores in ChromaDB
with rich metadata.
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
import json

# Document processing libraries
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

# Local imports
from llm_backend import LLMBackend
from knowledge_db import KnowledgeDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentScanner:
    """
    Scans directories for legal documents, extracts text, classifies them,
    and stores in ChromaDB and KnowledgeDB.
    """

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.doc'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
    CHUNK_SIZE = 2000  # Characters to send to LLM for classification

    def __init__(
        self,
        llm: LLMBackend,
        chroma_collection,
        knowledge_db: KnowledgeDB,
        scan_paths: List[str] = None,
        user_id: int = 0,
    ):
        self.llm = llm
        self.collection = chroma_collection
        self.knowledge_db = knowledge_db
        self.scan_paths = scan_paths or self._get_default_scan_paths()
        self.user_id = user_id

        # Statistics
        self.stats = {
            "files_found": 0,
            "files_scanned": 0,
            "files_indexed": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "errors": []
        }

    def _get_default_scan_paths(self) -> List[str]:
        """Get default scan paths from environment or use fallback."""
        env_paths = os.getenv("SCAN_PATHS", "")
        if env_paths:
            return [p.strip() for p in env_paths.split(",") if p.strip()]

        # Default paths
        defaults = [
            "C:/Users/SJK/Documents/",
            "E:/etdocumentsdownload/"
        ]
        # Filter to only existing paths
        return [p for p in defaults if os.path.exists(p)]

    def discover_documents(self) -> List[str]:
        """
        Recursively discover all supported documents in scan paths.
        Returns list of file paths.
        """
        discovered = []

        for scan_path in self.scan_paths:
            if not os.path.exists(scan_path):
                logger.warning(f"Scan path does not exist: {scan_path}")
                continue

            logger.info(f"Scanning directory: {scan_path}")

            try:
                for root, dirs, files in os.walk(scan_path):
                    # Skip certain directories
                    dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._is_supported_document(file_path):
                            discovered.append(file_path)
                            self.stats["files_found"] += 1

            except Exception as e:
                logger.error(f"Error scanning {scan_path}: {e}")
                self.stats["errors"].append(f"Scan error in {scan_path}: {str(e)}")

        logger.info(f"Discovered {len(discovered)} documents")
        return discovered

    def _should_skip_dir(self, dirname: str) -> bool:
        """Check if directory should be skipped."""
        skip_patterns = {
            '$RECYCLE.BIN', 'System Volume Information', 'Windows',
            'Program Files', 'Program Files (x86)', 'AppData',
            '__pycache__', '.git', '.venv', 'node_modules', 'venv',
            'finetune_venv', 'chroma_db'
        }
        return dirname in skip_patterns or dirname.startswith('.')

    def _is_supported_document(self, file_path: str) -> bool:
        """Check if file is a supported document type."""
        ext = Path(file_path).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return False

        # Check file size
        try:
            size = os.path.getsize(file_path)
            if size > self.MAX_FILE_SIZE:
                logger.debug(f"Skipping large file: {file_path} ({size} bytes)")
                return False
            if size == 0:
                return False
        except Exception:
            return False

        return True

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file for change detection."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {file_path}: {e}")
            return ""

    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from document file."""
        ext = Path(file_path).suffix.lower()

        try:
            if ext == '.txt':
                return self._extract_text_txt(file_path)
            elif ext == '.pdf':
                return self._extract_text_pdf(file_path)
            elif ext in {'.docx', '.doc'}:
                return self._extract_text_docx(file_path)
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return None
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            self.stats["errors"].append(f"Text extraction error in {file_path}: {str(e)}")
            return None

    def _extract_text_txt(self, file_path: str) -> str:
        """Extract text from .txt file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _extract_text_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from PDF file."""
        if PyPDF2 is None:
            logger.error("PyPDF2 not installed")
            return None

        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return None

    def _extract_text_docx(self, file_path: str) -> Optional[str]:
        """Extract text from DOCX file."""
        if DocxDocument is None:
            logger.error("python-docx not installed")
            return None

        try:
            doc = DocxDocument(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            return None

    def classify_document(self, text: str, file_name: str) -> Dict:
        """
        Use LLM to classify document type and extract key information.
        Returns dict with: document_type, document_subtype, extracted_fields, sections, confidence
        """
        # Truncate text for classification
        text_sample = text[:self.CHUNK_SIZE]

        prompt = f"""Analyze this legal document and extract the following information in JSON format:

{{
    "document_type": "contract|employment|nda|lease|filing|brief|memo|correspondence|other",
    "document_subtype": "specific type (e.g., Independent Contractor Agreement, Commercial Lease, NDA, etc.)",
    "confidence": 0.0-1.0,
    "extracted_fields": {{
        "field_name": "extracted value",
        ...
    }},
    "sections": ["list of main section headings found"],
    "key_terms": ["important terms or clauses identified"]
}}

Extract all named parties, dates, amounts, locations, and other important fields.
Be as specific as possible with the document_subtype.

Filename: {file_name}

Document excerpt:

{text_sample}

Return ONLY valid JSON, no other text."""

        messages = [
            {
                "role": "system",
                "content": "You are a legal document classification expert. Always return valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = self.llm.chat(messages, temperature=0.1, max_tokens=2048)

            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                classification = json.loads(response[json_start:json_end])

                # Validate required fields
                if "document_subtype" not in classification:
                    classification["document_subtype"] = classification.get("document_type", "Unknown")
                if "extracted_fields" not in classification:
                    classification["extracted_fields"] = {}
                if "confidence" not in classification:
                    classification["confidence"] = 0.5

                return classification
            else:
                # Fallback
                return self._fallback_classification(file_name)

        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._fallback_classification(file_name)

    def _fallback_classification(self, file_name: str) -> Dict:
        """Fallback classification based on filename heuristics."""
        name_lower = file_name.lower()

        if any(term in name_lower for term in ['nda', 'confidentiality']):
            doc_type = "NDA / Confidentiality Agreement"
        elif any(term in name_lower for term in ['contract', 'agreement']):
            doc_type = "Contract / Agreement"
        elif any(term in name_lower for term in ['lease']):
            doc_type = "Lease Agreement"
        elif any(term in name_lower for term in ['employment', 'offer', 'severance']):
            doc_type = "Employment Agreement"
        else:
            doc_type = "Unknown Document"

        return {
            "document_type": "other",
            "document_subtype": doc_type,
            "confidence": 0.3,
            "extracted_fields": {},
            "sections": [],
            "key_terms": []
        }

    def index_document(
        self,
        file_path: str,
        text: str,
        classification: Dict,
        file_hash: str,
        file_size: int
    ) -> bool:
        """
        Index document in ChromaDB and record in KnowledgeDB.
        Returns True if successful.
        """
        try:
            # Chunk the text
            chunks = self._chunk_text(text)
            if not chunks:
                logger.warning(f"No chunks generated for {file_path}")
                return False

            # Generate unique IDs
            file_id = hashlib.md5(file_path.encode()).hexdigest()[:16]
            chunk_ids = [f"doc_{file_id}_chunk_{i}" for i in range(len(chunks))]

            # Prepare metadata
            document_type = classification.get("document_subtype", "Unknown")
            metadatas = [
                {
                    "source_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "chunk_index": i,
                    "document_type": document_type,
                    "document_type_category": classification.get("document_type", "other"),
                    "confidence": classification.get("confidence", 0.5),
                    "indexed_date": datetime.now().isoformat(),
                    "file_size": file_size,
                    "file_hash": file_hash,
                }
                for i in range(len(chunks))
            ]

            # Add to ChromaDB
            self.collection.add(
                documents=chunks,
                ids=chunk_ids,
                metadatas=metadatas
            )

            # Record in KnowledgeDB
            self.knowledge_db.add_scanned_file(
                file_path=file_path,
                file_hash=file_hash,
                file_size=file_size,
                document_type=document_type,
                extracted_fields=classification.get("extracted_fields", {}),
                status="indexed",
                user_id=self.user_id,
            )

            logger.info(f"Indexed {len(chunks)} chunks from {os.path.basename(file_path)}")
            return True

        except Exception as e:
            logger.error(f"Indexing error for {file_path}: {e}")
            self.stats["errors"].append(f"Indexing error in {file_path}: {str(e)}")
            return False

    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap

        return chunks

    def scan_and_index(self, progress_callback=None) -> Dict:
        """
        Main scanning method: discover, classify, and index all documents.
        Returns statistics dict.
        """
        scan_id = self.knowledge_db.start_scan(user_id=self.user_id)
        logger.info("Starting document scan...")

        # Reset stats
        self.stats = {
            "files_found": 0,
            "files_scanned": 0,
            "files_indexed": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "errors": []
        }

        # Discover documents
        documents = self.discover_documents()

        # Process each document
        for i, file_path in enumerate(documents):
            try:
                # Progress callback
                if progress_callback:
                    progress_callback(i + 1, len(documents), os.path.basename(file_path))

                # Check if already indexed
                file_hash = self._compute_file_hash(file_path)
                if not file_hash:
                    self.stats["files_failed"] += 1
                    continue

                if self.knowledge_db.is_file_scanned(file_path, file_hash, user_id=self.user_id):
                    logger.debug(f"Skipping already indexed: {file_path}")
                    self.stats["files_skipped"] += 1
                    continue

                # Extract text
                text = self.extract_text(file_path)
                if not text or len(text) < 100:
                    logger.warning(f"Insufficient text extracted from {file_path}")
                    self.stats["files_failed"] += 1
                    continue

                self.stats["files_scanned"] += 1

                # Classify document
                classification = self.classify_document(text, os.path.basename(file_path))

                # Index document
                file_size = os.path.getsize(file_path)
                success = self.index_document(file_path, text, classification, file_hash, file_size)

                if success:
                    self.stats["files_indexed"] += 1
                else:
                    self.stats["files_failed"] += 1

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                self.stats["errors"].append(f"Processing error in {file_path}: {str(e)}")
                self.stats["files_failed"] += 1

        # Update scan history
        self.knowledge_db.end_scan(
            scan_id=scan_id,
            files_scanned=self.stats["files_scanned"],
            files_indexed=self.stats["files_indexed"],
            files_failed=self.stats["files_failed"],
            errors="\n".join(self.stats["errors"][:10])  # Store first 10 errors
        )

        logger.info(f"Scan complete: {self.stats}")
        return self.stats

    def build_learned_templates(self):
        """
        Aggregate field information from all indexed documents to build
        learned templates for each document type.
        """
        logger.info("Building learned templates from indexed documents...")

        # Get all unique document types
        all_types = self.knowledge_db.get_all_document_types(user_id=self.user_id)

        for type_info in all_types:
            document_type = type_info["type"]
            logger.info(f"Processing learned template for: {document_type}")

            # Get all files of this type
            files = self.knowledge_db.get_scanned_files_by_type(document_type, user_id=self.user_id)

            if not files:
                continue

            # Aggregate fields across all documents
            field_frequencies = {}
            all_field_names = set()

            for file_info in files:
                extracted_fields = file_info["extracted_fields"]
                for field_name, field_value in extracted_fields.items():
                    all_field_names.add(field_name)
                    field_frequencies[field_name] = field_frequencies.get(field_name, 0) + 1

            # Calculate confidence scores (frequency / total documents)
            total_docs = len(files)
            field_confidence = {
                name: freq / total_docs
                for name, freq in field_frequencies.items()
            }

            # Sort fields by frequency
            sorted_fields = sorted(
                field_confidence.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Build field definitions (only include fields appearing in 30%+ of documents)
            learned_fields = []
            for field_name, confidence in sorted_fields:
                if confidence >= 0.3:  # Appears in at least 30% of documents
                    learned_fields.append({
                        "key": field_name.lower().replace(" ", "_"),
                        "label": field_name.replace("_", " ").title(),
                        "type": "text",
                        "confidence": confidence,
                        "frequency": field_frequencies[field_name],
                        "help": f"Learned from {field_frequencies[field_name]} documents"
                    })

            # Save learned template
            self.knowledge_db.update_learned_template(
                document_type=document_type,
                fields=learned_fields,
                field_frequencies=field_frequencies,
                sample_count=total_docs,
                user_id=self.user_id,
            )

            logger.info(f"Created learned template for {document_type} with {len(learned_fields)} fields from {total_docs} documents")

        logger.info("Learned templates built successfully")
