"""Text extraction, quality filtering, and document type classification."""

import logging
import os
import re
import sys
import warnings
from pathlib import Path

from config import MIN_TEXT_LENGTH, MAX_NON_ASCII_RATIO

# Suppress noisy PyPDF2 warnings (unknown widths, XFormObject, etc.)
warnings.filterwarnings("ignore")
logging.getLogger("PyPDF2").setLevel(logging.CRITICAL)


# ======================================================================
# Text extraction (adapted from streamlit_app.py:131-148 for disk files)
# ======================================================================

def extract_text_from_file(file_path: Path) -> str | None:
    """Extract text from a PDF, DOCX, or TXT file on disk.

    Returns the extracted text, or None if extraction fails or the file
    type is unsupported.
    """
    suffix = file_path.suffix.lower()
    try:
        if suffix == ".txt":
            return file_path.read_text(encoding="utf-8", errors="replace")

        elif suffix == ".pdf":
            import PyPDF2
            # Suppress C-level stderr output from PyPDF2
            old_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")
            try:
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    return "\n".join(page.extract_text() or "" for page in reader.pages)
            finally:
                sys.stderr.close()
                sys.stderr = old_stderr

        elif suffix == ".docx":
            import docx
            doc = docx.Document(str(file_path))
            return "\n".join(p.text for p in doc.paragraphs)

    except Exception as e:
        print(f"  [WARN] Could not extract text from {file_path.name}: {e}")
    return None


# ======================================================================
# Quality filters
# ======================================================================

def passes_quality_filter(text: str) -> bool:
    """Return True if the document text meets minimum quality standards."""
    if len(text) < MIN_TEXT_LENGTH:
        return False

    non_ascii = sum(1 for c in text if ord(c) > 127)
    if non_ascii / len(text) > MAX_NON_ASCII_RATIO:
        return False

    return True


# ======================================================================
# Document type classification (keyword heuristics)
# ======================================================================

_CONTRACT_PATTERNS = re.compile(
    r"\b(AGREEMENT|WHEREAS|HEREBY AGREES|PARTY OF THE FIRST PART|"
    r"TERMS AND CONDITIONS|INDEMNIF|COVENANT|RECITALS|NOW,?\s*THEREFORE|"
    r"IN WITNESS WHEREOF|EXECUTED AS OF)\b",
    re.IGNORECASE,
)

_MEMO_PATTERNS = re.compile(
    r"(^|\n)\s*(MEMORANDUM|MEMO)\b|"
    r"(^|\n)\s*TO\s*:|"
    r"(^|\n)\s*FROM\s*:|"
    r"(^|\n)\s*RE\s*:|"
    r"\bQUESTIONS?\s+PRESENTED\b|"
    r"\bBRIEF\s+ANSWER\b",
    re.IGNORECASE,
)

_BRIEF_PATTERNS = re.compile(
    r"\b(MOTION TO|BRIEF IN|MEMORANDUM OF LAW|ARGUMENT|"
    r"STATEMENT OF FACTS|COMES NOW|RESPECTFULLY SUBMITTED|"
    r"IN THE .{0,30} COURT|PLAINTIFF|DEFENDANT|APPELLEE|APPELLANT|"
    r"PRAYER FOR RELIEF|WHEREFORE)\b",
    re.IGNORECASE,
)

_FILING_PATTERNS = re.compile(
    r"\b(ARTICLES OF|CERTIFICATE OF|CERTIFICATE OF INCORPORATION|"
    r"ARTICLES OF ORGANIZATION|ANNUAL REPORT|CERTIFICATE OF AMENDMENT|"
    r"CERTIFICATE OF FORMATION|REGISTERED AGENT|INCORPORATOR|"
    r"AUTHORIZED SHARES|CERTIFICATE OF GOOD STANDING)\b",
    re.IGNORECASE,
)

_SETTLEMENT_PATTERNS = re.compile(
    r"\b(SETTLEMENT AGREEMENT|RELEASE AND SETTLEMENT|"
    r"MUTUAL RELEASE|SETTLEMENT AND RELEASE|CONFIDENTIAL SETTLEMENT|"
    r"CONSIDERATION OF THE MUTUAL|SETTLE AND COMPROMISE)\b",
    re.IGNORECASE,
)


def classify_document(text: str) -> str:
    """Classify a document into a legal document type using keyword heuristics.

    Returns one of: contract, memo, brief, filing, settlement, legal_document
    """
    # Score each category by number of pattern matches in the first 3000 chars
    sample = text[:3000]

    scores = {
        "contract": len(_CONTRACT_PATTERNS.findall(sample)),
        "memo": len(_MEMO_PATTERNS.findall(sample)),
        "brief": len(_BRIEF_PATTERNS.findall(sample)),
        "filing": len(_FILING_PATTERNS.findall(sample)),
        "settlement": len(_SETTLEMENT_PATTERNS.findall(sample)),
    }

    best = max(scores, key=scores.get)
    if scores[best] >= 2:
        return best

    # Fallback: generic legal document
    return "legal_document"


# ======================================================================
# Extract context from document header
# ======================================================================

def extract_header_context(text: str, doc_type: str) -> str:
    """Pull a short context string from the document header for the training prompt."""
    lines = text[:2000].split("\n")
    # Grab non-empty lines from the top
    header_lines = [ln.strip() for ln in lines[:20] if ln.strip()]

    if doc_type == "contract":
        # Look for title line like "SERVICE AGREEMENT" or "MASTER LEASE AGREEMENT"
        for ln in header_lines[:10]:
            if "AGREEMENT" in ln.upper() or "CONTRACT" in ln.upper():
                return ln.strip()
        return "Agreement"

    elif doc_type == "memo":
        # Look for RE: line
        for ln in header_lines[:15]:
            if re.match(r"^\s*RE\s*:", ln, re.IGNORECASE):
                return ln.strip()
        return "Internal Legal Memorandum"

    elif doc_type == "brief":
        # Look for motion type
        for ln in header_lines[:15]:
            if "MOTION" in ln.upper() or "BRIEF" in ln.upper():
                return ln.strip()
        return "Legal Brief"

    elif doc_type == "filing":
        for ln in header_lines[:10]:
            upper = ln.upper()
            if "ARTICLES" in upper or "CERTIFICATE" in upper:
                return ln.strip()
        return "Corporate Filing"

    elif doc_type == "settlement":
        return "Settlement Agreement"

    # Fallback: use first non-empty header line
    return header_lines[0] if header_lines else "Legal Document"
