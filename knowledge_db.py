"""
Knowledge Database — Learned Templates Storage using SQLite.

Stores aggregated field information learned from scanning real documents.
Provides a structured way to track which fields appear most frequently
for each document type.
"""

import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime
import os


class KnowledgeDB:
    """SQLite database for learned document templates and metadata."""

    def __init__(self, db_path: str = "./knowledge.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Learned templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type TEXT NOT NULL UNIQUE,
                fields JSON NOT NULL,
                field_frequencies JSON NOT NULL,
                sample_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Scanned files tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scanned_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                file_hash TEXT NOT NULL,
                file_size INTEGER,
                document_type TEXT,
                extracted_fields JSON,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'indexed'
            )
        """)

        # Scan history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_start TIMESTAMP,
                scan_end TIMESTAMP,
                files_scanned INTEGER DEFAULT 0,
                files_indexed INTEGER DEFAULT 0,
                files_failed INTEGER DEFAULT 0,
                errors TEXT,
                status TEXT DEFAULT 'running'
            )
        """)

        # Configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def get_learned_template(self, document_type: str) -> Optional[Dict]:
        """Retrieve learned template for a document type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT fields, field_frequencies, sample_count, last_updated
            FROM learned_templates
            WHERE document_type = ?
        """, (document_type,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "fields": json.loads(row[0]),
                "field_frequencies": json.loads(row[1]),
                "sample_count": row[2],
                "last_updated": row[3]
            }
        return None

    def update_learned_template(
        self,
        document_type: str,
        fields: List[Dict],
        field_frequencies: Dict[str, int],
        sample_count: int
    ):
        """Update or create a learned template."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO learned_templates
            (document_type, fields, field_frequencies, sample_count, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(document_type) DO UPDATE SET
                fields = excluded.fields,
                field_frequencies = excluded.field_frequencies,
                sample_count = excluded.sample_count,
                last_updated = excluded.last_updated
        """, (
            document_type,
            json.dumps(fields),
            json.dumps(field_frequencies),
            sample_count,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def add_scanned_file(
        self,
        file_path: str,
        file_hash: str,
        file_size: int,
        document_type: str,
        extracted_fields: Dict,
        status: str = "indexed"
    ):
        """Record a scanned file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO scanned_files
                (file_path, file_hash, file_size, document_type, extracted_fields, scan_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path,
                file_hash,
                file_size,
                document_type,
                json.dumps(extracted_fields),
                datetime.now().isoformat(),
                status
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            # File already scanned, update it
            cursor.execute("""
                UPDATE scanned_files
                SET file_hash = ?, file_size = ?, document_type = ?,
                    extracted_fields = ?, scan_date = ?, status = ?
                WHERE file_path = ?
            """, (
                file_hash,
                file_size,
                document_type,
                json.dumps(extracted_fields),
                datetime.now().isoformat(),
                status,
                file_path
            ))
            conn.commit()

        conn.close()

    def is_file_scanned(self, file_path: str, file_hash: str) -> bool:
        """Check if a file has already been scanned with the same content."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM scanned_files
            WHERE file_path = ? AND file_hash = ?
        """, (file_path, file_hash))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def get_scanned_files_by_type(self, document_type: str) -> List[Dict]:
        """Get all scanned files of a specific type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path, file_size, extracted_fields, scan_date
            FROM scanned_files
            WHERE document_type = ?
            ORDER BY scan_date DESC
        """, (document_type,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "file_path": row[0],
                "file_size": row[1],
                "extracted_fields": json.loads(row[2]),
                "scan_date": row[3]
            }
            for row in rows
        ]

    def get_all_document_types(self) -> List[str]:
        """Get all document types that have learned templates."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT document_type, sample_count
            FROM learned_templates
            ORDER BY sample_count DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [{"type": row[0], "count": row[1]} for row in rows]

    def start_scan(self) -> int:
        """Start a new scan session and return scan_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scan_history (scan_start, status)
            VALUES (?, 'running')
        """, (datetime.now().isoformat(),))

        scan_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return scan_id

    def end_scan(
        self,
        scan_id: int,
        files_scanned: int,
        files_indexed: int,
        files_failed: int,
        errors: str = ""
    ):
        """Mark a scan session as complete."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE scan_history
            SET scan_end = ?,
                files_scanned = ?,
                files_indexed = ?,
                files_failed = ?,
                errors = ?,
                status = 'completed'
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            files_scanned,
            files_indexed,
            files_failed,
            errors,
            scan_id
        ))

        conn.commit()
        conn.close()

    def get_scan_history(self, limit: int = 10) -> List[Dict]:
        """Get recent scan history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT scan_start, scan_end, files_scanned, files_indexed,
                   files_failed, status, errors
            FROM scan_history
            ORDER BY scan_start DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "scan_start": row[0],
                "scan_end": row[1],
                "files_scanned": row[2],
                "files_indexed": row[3],
                "files_failed": row[4],
                "status": row[5],
                "errors": row[6]
            }
            for row in rows
        ]

    def get_stats(self) -> Dict:
        """Get overall knowledge base statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total documents indexed
        cursor.execute("SELECT COUNT(*) FROM scanned_files WHERE status = 'indexed'")
        total_docs = cursor.fetchone()[0]

        # Total document types learned
        cursor.execute("SELECT COUNT(*) FROM learned_templates")
        total_types = cursor.fetchone()[0]

        # Last scan time
        cursor.execute("SELECT MAX(scan_end) FROM scan_history WHERE status = 'completed'")
        last_scan = cursor.fetchone()[0]

        # Total scans
        cursor.execute("SELECT COUNT(*) FROM scan_history")
        total_scans = cursor.fetchone()[0]

        conn.close()

        return {
            "total_documents": total_docs,
            "document_types": total_types,
            "last_scan": last_scan,
            "total_scans": total_scans
        }

    def set_config(self, key: str, value: str):
        """Set a configuration value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO config (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (key, value, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_config(self, key: str, default: str = None) -> Optional[str]:
        """Get a configuration value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()

        return row[0] if row else default
