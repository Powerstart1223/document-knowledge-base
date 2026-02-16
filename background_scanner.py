"""
Background Scanner ? Runs continuous document scanning in a background thread.

Monitors configured directories for new/modified files and incrementally
indexes them without blocking the main Streamlit application.
"""

import threading
import logging
from typing import Optional, Callable
from datetime import datetime, timedelta
import os

from document_scanner import DocumentScanner
from llm_backend import LLMBackend
from knowledge_db import KnowledgeDB

logger = logging.getLogger(__name__)


class BackgroundScanner:
    """
    Background service that periodically scans for and indexes new documents.
    Runs in a separate thread to avoid blocking the main application.
    """

    def __init__(
        self,
        user_id: int,
        llm: LLMBackend,
        chroma_collection,
        knowledge_db: KnowledgeDB,
        scan_paths: list = None,
        scan_interval_minutes: int = 30,
        auto_start: bool = False
    ):
        self.user_id = user_id
        self.llm = llm
        self.collection = chroma_collection
        self.knowledge_db = knowledge_db
        self.scan_paths = scan_paths
        self.scan_interval_minutes = scan_interval_minutes

        # Thread control
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        # Status tracking
        self.status = {
            "is_running": False,
            "last_scan_start": None,
            "last_scan_end": None,
            "last_scan_stats": None,
            "next_scan_time": None,
            "current_progress": None,
            "error": None
        }

        # Callbacks
        self._progress_callback: Optional[Callable] = None

        if auto_start:
            self.start()

    def set_progress_callback(self, callback: Callable):
        """Set callback function for progress updates."""
        self._progress_callback = callback

    def start(self):
        """Start the background scanning thread."""
        if self._running:
            logger.warning("Background scanner is already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()
        self._running = True
        self.status["is_running"] = True
        logger.info("Background scanner started for user_id=%s", self.user_id)

    def stop(self):
        """Stop the background scanning thread."""
        if not self._running:
            return

        logger.info("Stopping background scanner for user_id=%s...", self.user_id)
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=5.0)

        self._running = False
        self.status["is_running"] = False
        logger.info("Background scanner stopped for user_id=%s", self.user_id)

    def is_running(self) -> bool:
        """Check if scanner is currently running."""
        return self._running

    def trigger_scan(self):
        """Manually trigger an immediate scan."""
        if not self._running:
            logger.warning("Cannot trigger scan - scanner not running")
            return

        # Signal to run scan immediately
        self.status["next_scan_time"] = datetime.now()

    def run_scan_once(self):
        """Run a single scan immediately (manual/admin use)."""
        self._run_scan()

    def _scan_loop(self):
        """Main scanning loop that runs in background thread."""
        logger.info(
            "Scan loop started for user_id=%s (interval: %s minutes)",
            self.user_id,
            self.scan_interval_minutes,
        )

        # Initial delay before first scan (give app time to start)
        initial_delay = 60  # 1 minute
        if self._stop_event.wait(initial_delay):
            return

        while not self._stop_event.is_set():
            try:
                # Run scan
                self._run_scan()

                # Calculate next scan time
                next_scan = datetime.now() + timedelta(minutes=self.scan_interval_minutes)
                self.status["next_scan_time"] = next_scan.isoformat()

                # Sleep until next scan (or stop signal)
                sleep_seconds = self.scan_interval_minutes * 60
                if self._stop_event.wait(sleep_seconds):
                    break  # Stop signal received

            except Exception as e:
                logger.error("Error in scan loop: %s", e)
                self.status["error"] = str(e)

                # Wait a bit before retrying after error
                if self._stop_event.wait(300):  # 5 minutes
                    break

        logger.info("Scan loop ended for user_id=%s", self.user_id)

    def _run_scan(self):
        """Execute a single scan operation."""
        logger.info("Starting background scan for user_id=%s...", self.user_id)

        self.status["last_scan_start"] = datetime.now().isoformat()
        self.status["current_progress"] = {"current": 0, "total": 0, "file": "Initializing..."}

        try:
            # Create scanner instance
            scanner = DocumentScanner(
                llm=self.llm,
                chroma_collection=self.collection,
                knowledge_db=self.knowledge_db,
                scan_paths=self.scan_paths,
                user_id=self.user_id,
            )

            # Run scan with progress callback
            def progress_callback(current, total, filename):
                self.status["current_progress"] = {
                    "current": current,
                    "total": total,
                    "file": filename
                }
                if self._progress_callback:
                    self._progress_callback(current, total, filename)

            stats = scanner.scan_and_index(progress_callback=progress_callback)

            # Build learned templates if we indexed new documents
            if stats["files_indexed"] > 0:
                logger.info("Building learned templates for user_id=%s...", self.user_id)
                scanner.build_learned_templates()

            # Update status
            self.status["last_scan_end"] = datetime.now().isoformat()
            self.status["last_scan_stats"] = stats
            self.status["current_progress"] = None
            self.status["error"] = None

            logger.info("Background scan completed for user_id=%s: %s", self.user_id, stats)

        except Exception as e:
            logger.error("Scan failed for user_id=%s: %s", self.user_id, e)
            self.status["last_scan_end"] = datetime.now().isoformat()
            self.status["error"] = str(e)
            self.status["current_progress"] = None

    def get_status(self) -> dict:
        """Get current scanner status."""
        return {
            **self.status,
            "scan_interval_minutes": self.scan_interval_minutes,
            "scan_paths": self.scan_paths,
            "user_id": self.user_id,
        }


class ScannerManager:
    """
    Manager for background scanners keyed by user_id.
    Ensures scanner state is isolated per authenticated user.
    """

    _instances: dict[int, BackgroundScanner] = {}

    @classmethod
    def initialize(
        cls,
        user_id: int,
        llm: LLMBackend,
        chroma_collection,
        knowledge_db: KnowledgeDB,
        scan_paths: list = None,
        scan_interval_minutes: int = None,
        auto_start: bool = None
    ) -> BackgroundScanner:
        """Initialize the background scanner for a specific user."""

        # Get configuration from environment
        if scan_interval_minutes is None:
            scan_interval_minutes = int(os.getenv("SCAN_INTERVAL_MINUTES", "30"))

        if auto_start is None:
            auto_start = os.getenv("AUTO_SCAN_ENABLED", "true").lower() == "true"

        if user_id not in cls._instances:
            cls._instances[user_id] = BackgroundScanner(
                user_id=user_id,
                llm=llm,
                chroma_collection=chroma_collection,
                knowledge_db=knowledge_db,
                scan_paths=scan_paths,
                scan_interval_minutes=scan_interval_minutes,
                auto_start=auto_start
            )
            logger.info("Background scanner initialized for user_id=%s", user_id)
        else:
            logger.info("Using existing background scanner instance for user_id=%s", user_id)

        return cls._instances[user_id]

    @classmethod
    def get_instance(cls, user_id: int) -> Optional[BackgroundScanner]:
        """Get the current scanner instance for a user (if initialized)."""
        return cls._instances.get(user_id)

    @classmethod
    def shutdown(cls, user_id: Optional[int] = None):
        """Shutdown one user's scanner or all scanners."""
        if user_id is not None:
            scanner = cls._instances.get(user_id)
            if scanner:
                scanner.stop()
                del cls._instances[user_id]
                logger.info("Background scanner shut down for user_id=%s", user_id)
            return

        for uid, scanner in list(cls._instances.items()):
            scanner.stop()
            del cls._instances[uid]
        logger.info("All background scanners shut down")
