"""Scan document directories, extract text, classify, and build training JSONL.

Usage:
    python prepare_data.py
    python prepare_data.py --extra-dir C:\\path\\to\\extra\\corpus
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import warnings
from pathlib import Path

# Suppress all PyPDF2 noise before it's imported
warnings.filterwarnings("ignore")
logging.getLogger("PyPDF2").setLevel(logging.CRITICAL)
# Redirect stderr to devnull during PDF processing to suppress C-level output
_devnull = open(os.devnull, "w")

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCUMENT_DIRS,
    MAX_DOC_CHARS,
    SUPPORTED_EXTENSIONS,
    TRAINING_DATA_DIR,
    TRAINING_DATA_FILE,
    TRAINING_SYSTEM_PROMPT,
)
from utils import (
    classify_document,
    extract_header_context,
    extract_text_from_file,
    passes_quality_filter,
)


# ======================================================================
# Deduplication
# ======================================================================

def _file_fingerprint(path: Path) -> str:
    """Create a dedup fingerprint from filename + size + first 10KB hash."""
    h = hashlib.md5()
    h.update(path.name.encode())
    h.update(str(path.stat().st_size).encode())
    with open(path, "rb") as f:
        h.update(f.read(10240))
    return h.hexdigest()


# ======================================================================
# Chunking at section boundaries
# ======================================================================

_SECTION_BREAK = re.compile(
    r"\n\s*(?:"
    r"\d+\.\s|"                # "1. ", "2. "
    r"[IVXLC]+\.\s|"          # "I. ", "II. "
    r"ARTICLE\s|"             # "ARTICLE "
    r"SECTION\s|"             # "SECTION "
    r"[A-Z]{2,}[:\.]|"        # "DEFINITIONS:", "RECITALS."
    r"\n\s*\n"                 # double newline
    r")",
    re.IGNORECASE,
)


def chunk_document(text: str) -> list[str]:
    """Split long documents into chunks at natural section boundaries."""
    if len(text) <= MAX_DOC_CHARS:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE

        if end >= len(text):
            chunks.append(text[start:])
            break

        # Look for a section break near the end of the chunk
        search_start = max(start + CHUNK_SIZE - 1000, start)
        search_region = text[search_start:end + 500]
        breaks = list(_SECTION_BREAK.finditer(search_region))

        if breaks:
            # Use the last break in the region
            best = breaks[-1]
            end = search_start + best.start()
        else:
            # Fall back to last paragraph break
            last_para = text.rfind("\n\n", start, end + 500)
            if last_para > start:
                end = last_para

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - CHUNK_OVERLAP

    return chunks


# ======================================================================
# Build ShareGPT-format training example
# ======================================================================

_DOC_TYPE_LABELS = {
    "contract": "contract",
    "memo": "legal memorandum",
    "brief": "legal brief",
    "filing": "corporate filing",
    "settlement": "settlement agreement",
    "legal_document": "legal document",
}


def build_training_example(text: str, doc_type: str, context: str, chunk_idx: int = 0) -> dict:
    """Build a single ShareGPT conversation training example."""
    label = _DOC_TYPE_LABELS.get(doc_type, "legal document")

    if chunk_idx > 0:
        user_content = f"Continue drafting the {label}: {context} (section {chunk_idx + 1})"
    else:
        user_content = f"Draft a {label}: {context}"

    return {
        "conversations": [
            {"role": "system", "content": TRAINING_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": text},
        ]
    }


# ======================================================================
# Main pipeline
# ======================================================================

def scan_files(document_dirs: list[Path]) -> list[Path]:
    """Recursively scan configured directories for supported files."""
    files = []
    for directory in document_dirs:
        if not directory.exists():
            print(f"  [SKIP] Directory not found: {directory}")
            continue
        for ext in SUPPORTED_EXTENSIONS:
            files.extend(directory.rglob(f"*{ext}"))
    return files


def main():
    parser = argparse.ArgumentParser(description="Build fine-tuning dataset from legal documents")
    parser.add_argument(
        "--extra-dir",
        action="append",
        default=[],
        help="Additional directory to scan (can be provided multiple times)",
    )
    parser.add_argument(
        "--skip-default-dirs",
        action="store_true",
        help="Only scan --extra-dir locations and ignore DOCUMENT_DIRS from config.py",
    )
    args = parser.parse_args()

    document_dirs: list[Path] = []
    if not args.skip_default_dirs:
        document_dirs.extend(DOCUMENT_DIRS)
    document_dirs.extend(Path(p).expanduser() for p in args.extra_dir if p)

    print("=" * 60)
    print("LEGAL DOCUMENT TRAINING DATA PREPARATION")
    print("=" * 60)

    # 1. Scan for files
    print("\n[1/5] Scanning directories for documents...")
    all_files = scan_files(document_dirs)
    print(f"  Found {len(all_files)} files")

    if not all_files:
        print("  ERROR: No files found. Check DOCUMENT_DIRS in config.py")
        sys.exit(1)

    # 2. Deduplicate
    print("\n[2/5] Deduplicating...")
    seen = set()
    unique_files = []
    for f in all_files:
        try:
            fp = _file_fingerprint(f)
            if fp not in seen:
                seen.add(fp)
                unique_files.append(f)
        except Exception:
            continue
    dupes = len(all_files) - len(unique_files)
    print(f"  {len(unique_files)} unique files ({dupes} duplicates removed)")

    # 3. Extract and filter
    print("\n[3/5] Extracting text and filtering...")
    documents = []
    skipped_extract = 0
    skipped_quality = 0

    for i, fpath in enumerate(unique_files, 1):
        if i % 200 == 0:
            print(f"  Processing {i}/{len(unique_files)}...")

        text = extract_text_from_file(fpath)
        if text is None:
            skipped_extract += 1
            continue

        if not passes_quality_filter(text):
            skipped_quality += 1
            continue

        doc_type = classify_document(text)
        context = extract_header_context(text, doc_type)
        documents.append((text, doc_type, context))

    print(f"  Extracted: {len(documents)} documents")
    print(f"  Skipped (extraction failed): {skipped_extract}")
    print(f"  Skipped (quality filter): {skipped_quality}")

    # 4. Classify summary
    print("\n[4/5] Document type distribution:")
    type_counts = {}
    for _, dt, _ in documents:
        type_counts[dt] = type_counts.get(dt, 0) + 1
    for dt, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {dt:20s}: {count}")

    # 5. Build training examples
    print("\n[5/5] Building training examples...")
    TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)

    example_count = 0
    with open(TRAINING_DATA_FILE, "w", encoding="utf-8") as out:
        for text, doc_type, context in documents:
            chunks = chunk_document(text)
            for idx, chunk in enumerate(chunks):
                example = build_training_example(chunk, doc_type, context, idx)
                out.write(json.dumps(example, ensure_ascii=False) + "\n")
                example_count += 1

    print(f"\n  Wrote {example_count} training examples")
    print(f"  Output: {TRAINING_DATA_FILE}")

    print("\n" + "=" * 60)
    print("DATA PREPARATION COMPLETE")
    print("=" * 60)
    return example_count


if __name__ == "__main__":
    main()
