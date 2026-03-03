"""Build a local corpus for fine-tuning from uploads and SEC EDGAR.

Usage:
    python build_training_corpus.py --include-uploads --include-edgar
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api_clients import SECEdgarClient

try:
    import PyPDF2
except Exception:  # pragma: no cover
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except Exception:  # pragma: no cover
    DocxDocument = None

DEFAULT_UPLOADS_DIR = PROJECT_ROOT / "uploads"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "finetune_output" / "corpus"


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _extract_from_upload(path: Path, max_chars: int) -> str:
    ext = path.suffix.lower()
    if ext in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    if ext == ".pdf" and PyPDF2 is not None:
        with path.open("rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() or "" for page in reader.pages)[:max_chars]
    if ext in {".doc", ".docx", ".docm"} and DocxDocument is not None:
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs)[:max_chars]
    return ""


def ingest_uploads(uploads_dir: Path, out_dir: Path, max_files: int, max_chars: int) -> int:
    if not uploads_dir.exists():
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    files = [
        p
        for p in uploads_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".txt", ".md", ".pdf", ".doc", ".docx", ".docm"}
    ]
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:max_files]

    written = 0
    for idx, path in enumerate(files, 1):
        try:
            text = _clean_text(_extract_from_upload(path, max_chars))
            if len(text) < 200:
                continue
            target = out_dir / f"upload_{idx:04d}_{path.stem[:48]}.txt"
            target.write_text(text, encoding="utf-8")
            written += 1
        except Exception:
            continue
    return written


def ingest_edgar(
    queries: list[str],
    out_dir: Path,
    max_filings_per_query: int,
    max_chars: int,
    user_agent: str,
) -> int:
    if not queries:
        return 0

    client = SECEdgarClient(user_agent=user_agent)
    if not client.is_configured():
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    seen_urls: set[str] = set()
    written = 0

    for query in queries:
        try:
            hits = client.search_filings(query=query, max_results=max_filings_per_query)
        except Exception:
            continue

        for filing in hits:
            url = filing.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                text = _clean_text(client.download_filing_text(url, max_chars=max_chars))
                if len(text) < 500:
                    continue
                slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", filing.get("entity_name", "entity"))[:32]
                target = out_dir / f"edgar_{written + 1:04d}_{slug}.txt"
                target.write_text(text, encoding="utf-8")
                meta = {
                    "query": query,
                    "url": url,
                    "entity_name": filing.get("entity_name"),
                    "form_type": filing.get("form_type"),
                    "file_date": filing.get("file_date"),
                }
                target.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
                written += 1
            except Exception:
                continue

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build fine-tuning corpus from uploads and EDGAR")
    parser.add_argument("--include-uploads", action="store_true")
    parser.add_argument("--include-edgar", action="store_true")
    parser.add_argument("--uploads-dir", default=str(DEFAULT_UPLOADS_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-upload-files", type=int, default=250)
    parser.add_argument("--max-filings-per-query", type=int, default=10)
    parser.add_argument("--max-chars-per-doc", type=int, default=20000)
    parser.add_argument(
        "--edgar-queries",
        default="material agreement,credit agreement,merger agreement,employment agreement,risk factors",
    )
    parser.add_argument("--sec-user-agent", default="")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    uploads_out = output_dir / "uploads"
    edgar_out = output_dir / "edgar"
    sec_user_agent = args.sec_user_agent.strip() or __import__("os").getenv("SEC_EDGAR_USER_AGENT", "")

    written_uploads = 0
    if args.include_uploads:
        written_uploads = ingest_uploads(
            uploads_dir=Path(args.uploads_dir),
            out_dir=uploads_out,
            max_files=args.max_upload_files,
            max_chars=args.max_chars_per_doc,
        )

    written_edgar = 0
    if args.include_edgar:
        queries = [q.strip() for q in args.edgar_queries.split(",") if q.strip()]
        written_edgar = ingest_edgar(
            queries=queries,
            out_dir=edgar_out,
            max_filings_per_query=args.max_filings_per_query,
            max_chars=args.max_chars_per_doc,
            user_agent=sec_user_agent,
        )

    manifest = {
        "uploads_docs": written_uploads,
        "edgar_docs": written_edgar,
        "output_dir": str(output_dir),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
