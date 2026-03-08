"""Scan accessible drives for legal documents and build an inventory + corpus.

This script is intended to run as part of the overnight weight-improvement
pipeline. It keeps the output practical:
- a normalized text corpus suitable for prepare_data.py
- a JSON summary of discovered documents grouped by practice side
- a markdown report for quick review
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from config import SUPPORTED_EXTENSIONS
from utils import classify_document, extract_text_from_file, passes_quality_filter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "artifacts" / "document_inventory" / "latest_inventory.json"
DEFAULT_MARKDOWN_FILE = PROJECT_ROOT / "artifacts" / "document_inventory" / "latest_inventory.md"
DEFAULT_CORPUS_DIR = PROJECT_ROOT / "finetune_output" / "corpus" / "discovered_drives"
SUPPORTED_SCAN_EXTENSIONS = set(SUPPORTED_EXTENSIONS) | {".doc", ".docm"}
SKIP_DIR_NAMES = {
    "$RECYCLE.BIN",
    "System Volume Information",
    "Windows",
    "Program Files",
    "Program Files (x86)",
    "ProgramData",
    "AppData",
    "__pycache__",
    ".git",
    ".venv",
    "node_modules",
    "venv",
    "finetune_venv",
    "chroma_db",
}
TRANSACTIONAL_TERMS = (
    "agreement", "contract", "purchase", "sale", "asset", "stock", "merger",
    "lease", "employment", "nda", "confidential", "credit", "loan", "board",
    "consent", "resolution", "formation", "operating agreement", "bylaws",
    "policy", "manual", "license", "assignment", "financing", "closing",
    "due diligence", "term sheet",
)
LITIGATION_TERMS = (
    "complaint", "petition", "answer", "motion", "brief", "opposition",
    "reply", "deposition", "subpoena", "interrogator", "request for production",
    "request for admission", "pleading", "affidavit", "declaration", "settlement",
    "release", "discovery", "trial", "hearing", "litigation", "lawsuit",
    "arbitration", "mediation", "exhibit",
)
SUBTYPE_PATTERNS = [
    ("Non-Disclosure Agreement", ("nda", "non-disclosure", "confidentiality")),
    ("Purchase Agreement", ("purchase agreement", "asset purchase", "stock purchase")),
    ("Merger Agreement", ("merger agreement", "merger", "acquisition")),
    ("Employment Agreement", ("employment agreement", "offer letter", "severance")),
    ("Lease Agreement", ("lease", "sublease")),
    ("Board / Corporate Governance", ("board consent", "board resolution", "minutes", "bylaws")),
    ("Financing Document", ("credit agreement", "loan agreement", "promissory note", "security agreement")),
    ("Litigation Pleading", ("complaint", "answer", "petition")),
    ("Motion / Brief", ("motion", "brief", "memorandum of law", "opposition")),
    ("Discovery", ("interrogator", "request for production", "request for admission", "subpoena", "deposition")),
    ("Settlement / Release", ("settlement", "release")),
]


def _windows_drive_roots() -> list[Path]:
    if os.name != "nt":
        return [Path("/")]
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    drives: list[Path] = []
    for idx in range(26):
        if mask & (1 << idx):
            drive = Path(f"{chr(65 + idx)}:/")
            if drive.exists():
                drives.append(drive)
    return drives


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("._")
    return cleaned or "document"


def _guess_practice_side(file_path: Path, text: str) -> str:
    sample = f"{file_path.name} {text[:3000]}".lower()
    transactional_hits = sum(term in sample for term in TRANSACTIONAL_TERMS)
    litigation_hits = sum(term in sample for term in LITIGATION_TERMS)
    if litigation_hits > transactional_hits:
        return "litigation"
    if transactional_hits > 0:
        return "transactional"
    return "other"


def _guess_subtype(file_path: Path, text: str, coarse_type: str) -> str:
    sample = f"{file_path.name}\n{text[:2500]}".lower()
    for label, patterns in SUBTYPE_PATTERNS:
        if any(pattern in sample for pattern in patterns):
            return label
    header = next((line.strip() for line in text.splitlines()[:12] if line.strip()), "")
    if header and 4 <= len(header) <= 120:
        return header
    coarse_labels = {
        "contract": "Contract / Agreement",
        "memo": "Memorandum",
        "brief": "Brief / Motion",
        "filing": "Corporate Filing",
        "settlement": "Settlement Agreement",
        "legal_document": "Legal Document",
    }
    return coarse_labels.get(coarse_type, "Legal Document")


def _discover_documents(roots: list[Path], max_total_files: int) -> list[Path]:
    discovered: list[Path] = []
    for root in roots:
        try:
            for current_root, dir_names, file_names in os.walk(root):
                dir_names[:] = [
                    name for name in dir_names
                    if name not in SKIP_DIR_NAMES and not name.startswith(".")
                ]
                current_path = Path(current_root)
                for file_name in file_names:
                    path = current_path / file_name
                    if path.suffix.lower() not in SUPPORTED_SCAN_EXTENSIONS:
                        continue
                    try:
                        size = path.stat().st_size
                    except OSError:
                        continue
                    if size <= 0 or size > 10 * 1024 * 1024:
                        continue
                    discovered.append(path)
                    if len(discovered) >= max_total_files:
                        return discovered
        except OSError:
            continue
    return discovered


def _load_creatable_document_types() -> list[dict[str, str]]:
    from document_generator import DOCUMENT_TYPES
    from extended_document_types import ADDITIONAL_DOCUMENT_TYPES

    names = set(DOCUMENT_TYPES.keys()) | set(ADDITIONAL_DOCUMENT_TYPES.keys())
    generated_path = PROJECT_ROOT / "document_types_generated.json"
    if generated_path.exists():
        try:
            payload = json.loads(generated_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                names.update(str(key) for key in payload.keys())
        except Exception:
            pass

    items: list[dict[str, str]] = []
    for name in sorted(names):
        side = _guess_practice_side(Path(name), name)
        items.append({"name": name, "practice_side": side})
    return items


def _write_markdown_report(report: dict, markdown_path: Path) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Document Landscape Inventory",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Scan Summary",
        "",
        f"- Scan roots: {', '.join(report['scan_roots']) or '(none)'}",
        f"- Files discovered: {report['stats']['files_discovered']}",
        f"- Files processed: {report['stats']['files_processed']}",
        f"- Corpus documents written: {report['stats']['corpus_documents_written']}",
        f"- Extraction failures: {report['stats']['extraction_failures']}",
        f"- Quality skips: {report['stats']['quality_skips']}",
        "",
        "## Discovered Documents By Practice Side",
        "",
    ]
    for side in ("transactional", "litigation", "other"):
        side_info = report["discovered_documents"]["by_practice_side"].get(side, {})
        lines.append(f"### {side.title()}")
        lines.append("")
        lines.append(f"- Documents: {side_info.get('document_count', 0)}")
        top_types = side_info.get("top_document_types", [])
        if top_types:
            lines.append("- Top document types:")
            for item in top_types:
                lines.append(f"  - {item['name']}: {item['count']}")
        sample_files = side_info.get("sample_files", [])
        if sample_files:
            lines.append("- Sample files:")
            for item in sample_files:
                lines.append(f"  - {item['subtype']} | {item['path']}")
        lines.append("")

    lines.extend([
        "## Creatable Document Types",
        "",
        f"- Total creatable types: {len(report['creatable_document_types'])}",
        "",
    ])
    by_side: dict[str, list[str]] = defaultdict(list)
    for item in report["creatable_document_types"]:
        by_side[item["practice_side"]].append(item["name"])
    for side in ("transactional", "litigation", "other"):
        lines.append(f"### {side.title()}")
        lines.append("")
        for name in by_side.get(side, []):
            lines.append(f"- {name}")
        lines.append("")

    markdown_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan drives for legal documents and build an inventory report")
    parser.add_argument("--output-file", default=str(DEFAULT_OUTPUT_FILE))
    parser.add_argument("--markdown-file", default=str(DEFAULT_MARKDOWN_FILE))
    parser.add_argument("--corpus-dir", default=str(DEFAULT_CORPUS_DIR))
    parser.add_argument("--max-total-files", type=int, default=5000)
    parser.add_argument("--scan-root", action="append", default=[], help="Optional root path to scan; may be passed multiple times")
    args = parser.parse_args()

    scan_roots = [Path(p) for p in args.scan_root if p] or _windows_drive_roots()
    corpus_dir = Path(args.corpus_dir)
    corpus_dir.mkdir(parents=True, exist_ok=True)

    print("[SCAN] Discovering legal documents across configured roots...")
    print("[SCAN] Roots: " + ", ".join(str(root) for root in scan_roots))
    discovered_files = _discover_documents(scan_roots, max_total_files=max(1, int(args.max_total_files)))
    print(f"[SCAN] Discovered {len(discovered_files)} candidate files")

    practice_counts: Counter[str] = Counter()
    subtype_counts: Counter[tuple[str, str]] = Counter()
    sample_files: dict[str, list[dict[str, str]]] = defaultdict(list)
    stats = {
        "files_discovered": len(discovered_files),
        "files_processed": 0,
        "corpus_documents_written": 0,
        "extraction_failures": 0,
        "quality_skips": 0,
    }

    for index, file_path in enumerate(discovered_files, start=1):
        if index % 100 == 0:
            print(f"[SCAN] Processing {index}/{len(discovered_files)}")
        text = extract_text_from_file(file_path)
        if not text:
            stats["extraction_failures"] += 1
            continue
        if not passes_quality_filter(text):
            stats["quality_skips"] += 1
            continue

        coarse_type = classify_document(text)
        side = _guess_practice_side(file_path, text)
        subtype = _guess_subtype(file_path, text, coarse_type)
        practice_counts[side] += 1
        subtype_counts[(side, subtype)] += 1
        stats["files_processed"] += 1

        side_dir = corpus_dir / side
        side_dir.mkdir(parents=True, exist_ok=True)
        out_name = f"{index:05d}_{_sanitize_filename(file_path.stem)}.txt"
        out_path = side_dir / out_name
        out_path.write_text(text, encoding="utf-8", errors="ignore")
        stats["corpus_documents_written"] += 1

        if len(sample_files[side]) < 25:
            sample_files[side].append({"path": str(file_path), "subtype": subtype})

    discovered_by_side: dict[str, dict] = {}
    for side in ("transactional", "litigation", "other"):
        top_types = [
            {"name": subtype, "count": count}
            for (entry_side, subtype), count in subtype_counts.most_common()
            if entry_side == side
        ][:50]
        discovered_by_side[side] = {
            "document_count": practice_counts.get(side, 0),
            "top_document_types": top_types,
            "sample_files": sample_files.get(side, []),
        }

    report = {
        "generated_at": datetime.now().isoformat(),
        "scan_roots": [str(root) for root in scan_roots],
        "stats": stats,
        "discovered_documents": {
            "by_practice_side": discovered_by_side,
        },
        "creatable_document_types": _load_creatable_document_types(),
    }

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_markdown_report(report, Path(args.markdown_file))

    print(f"[SCAN] Inventory report written to {output_path}")
    print(f"[SCAN] Corpus written to {corpus_dir}")


if __name__ == "__main__":
    main()
