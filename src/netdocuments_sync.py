"""
NetDocuments Synchronization Service
Handles syncing documents from NetDocuments to the knowledge base
"""

import os
import json
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from netdocuments_integration import NetDocumentsAPI
from document_processor import DocumentProcessor
from config import Config

class NetDocumentsSync:
    """Service for syncing NetDocuments to the knowledge base"""

    def __init__(self, rag_pipeline=None):
        self.api = NetDocumentsAPI()
        self.document_processor = DocumentProcessor()
        self.rag_pipeline = rag_pipeline
        self.sync_log_file = "netdocuments_sync.log"
        self.sync_state_file = "netdocuments_sync_state.json"

    def get_sync_state(self) -> Dict[str, Any]:
        """Load sync state from file"""
        if os.path.exists(self.sync_state_file):
            with open(self.sync_state_file, 'r') as f:
                return json.load(f)
        return {
            "last_sync": None,
            "synced_documents": {},
            "failed_documents": []
        }

    def save_sync_state(self, state: Dict[str, Any]):
        """Save sync state to file"""
        with open(self.sync_state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def log_sync_activity(self, message: str, level: str = "INFO"):
        """Log sync activity"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}\n"

        with open(self.sync_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        print(f"NetDocuments Sync - {log_entry.strip()}")

    def is_document_supported(self, doc_info: Dict[str, Any]) -> bool:
        """Check if document type is supported"""
        filename = doc_info.get("name", "")
        file_ext = Path(filename).suffix.lower()
        return file_ext in Config.SUPPORTED_EXTENSIONS

    def should_sync_document(self, doc_info: Dict[str, Any], sync_state: Dict[str, Any]) -> bool:
        """Determine if document should be synced"""
        doc_id = doc_info.get("id")
        if not doc_id:
            return False

        # Check if document type is supported
        if not self.is_document_supported(doc_info):
            return False

        # Check if document was already synced
        synced_docs = sync_state.get("synced_documents", {})
        if doc_id in synced_docs:
            # Check if document was modified since last sync
            last_modified = doc_info.get("modified")
            last_sync_modified = synced_docs[doc_id].get("modified")

            if last_modified and last_sync_modified:
                return last_modified > last_sync_modified

        return True

    def sync_document(self, doc_info: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Sync a single document to the knowledge base"""
        doc_id = doc_info.get("id")
        doc_name = doc_info.get("name", f"document_{doc_id}")

        try:
            self.log_sync_activity(f"Syncing document: {doc_name} (ID: {doc_id})")

            # Download document
            temp_file_path = self.api.download_document(doc_id)
            if not temp_file_path:
                error_msg = f"Failed to download document {doc_name}"
                self.log_sync_activity(error_msg, "ERROR")
                return False, error_msg

            # Process document
            try:
                documents = self.document_processor.process_document(temp_file_path)

                # Add NetDocuments metadata
                for doc in documents:
                    doc.metadata.update({
                        "netdocuments_id": doc_id,
                        "netdocuments_name": doc_name,
                        "netdocuments_modified": doc_info.get("modified"),
                        "netdocuments_author": doc_info.get("author"),
                        "netdocuments_workspace": doc_info.get("workspace"),
                        "sync_date": datetime.now().isoformat()
                    })

                # Add to knowledge base if RAG pipeline is available
                if self.rag_pipeline:
                    result = self.rag_pipeline.add_documents(documents)
                    if not result["success"]:
                        error_msg = f"Failed to add {doc_name} to knowledge base: {result['message']}"
                        self.log_sync_activity(error_msg, "ERROR")
                        return False, error_msg

                self.log_sync_activity(f"Successfully synced {doc_name} ({len(documents)} chunks)")
                return True, None

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            error_msg = f"Error syncing document {doc_name}: {str(e)}"
            self.log_sync_activity(error_msg, "ERROR")
            return False, error_msg

    def discover_documents(self, search_query: str = "*", max_results: int = 100,
                          cabinet_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover documents in NetDocuments"""
        try:
            self.log_sync_activity(f"Discovering documents with query: {search_query}")

            # Search for documents
            documents = self.api.search_documents(
                query=search_query,
                cabinet_id=cabinet_id,
                max_results=max_results
            )

            # Filter for supported document types
            supported_docs = [doc for doc in documents if self.is_document_supported(doc)]

            self.log_sync_activity(f"Found {len(supported_docs)} supported documents out of {len(documents)} total")
            return supported_docs

        except Exception as e:
            error_msg = f"Error discovering documents: {str(e)}"
            self.log_sync_activity(error_msg, "ERROR")
            return []

    def sync_recent_documents(self, days: int = 30, max_results: int = 50) -> Dict[str, Any]:
        """Sync recently modified documents"""
        try:
            self.log_sync_activity(f"Starting sync of documents modified in last {days} days")

            # Get recent documents
            recent_docs = self.api.get_recent_documents(days=days, max_results=max_results)

            return self.sync_documents(recent_docs)

        except Exception as e:
            error_msg = f"Error syncing recent documents: {str(e)}"
            self.log_sync_activity(error_msg, "ERROR")
            return {
                "success": False,
                "error": error_msg,
                "synced_count": 0,
                "failed_count": 0
            }

    def sync_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync a list of documents"""
        sync_state = self.get_sync_state()
        synced_count = 0
        failed_count = 0
        failed_docs = []

        self.log_sync_activity(f"Starting sync of {len(documents)} documents")

        for doc_info in documents:
            if not self.should_sync_document(doc_info, sync_state):
                continue

            success, error = self.sync_document(doc_info)

            if success:
                synced_count += 1
                # Update sync state
                doc_id = doc_info.get("id")
                sync_state["synced_documents"][doc_id] = {
                    "name": doc_info.get("name"),
                    "modified": doc_info.get("modified"),
                    "sync_date": datetime.now().isoformat()
                }
            else:
                failed_count += 1
                failed_docs.append({
                    "id": doc_info.get("id"),
                    "name": doc_info.get("name"),
                    "error": error
                })

        # Update sync state
        sync_state["last_sync"] = datetime.now().isoformat()
        sync_state["failed_documents"] = failed_docs
        self.save_sync_state(sync_state)

        result = {
            "success": failed_count == 0,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "failed_documents": failed_docs,
            "total_processed": len(documents)
        }

        self.log_sync_activity(
            f"Sync completed: {synced_count} synced, {failed_count} failed"
        )

        return result

    def get_cabinet_structure(self) -> Dict[str, Any]:
        """Get the structure of accessible cabinets, workspaces, and folders"""
        try:
            structure = {}
            cabinets = self.api.get_cabinets()

            for cabinet in cabinets:
                cabinet_id = cabinet.get("id")
                cabinet_name = cabinet.get("name", f"Cabinet {cabinet_id}")

                structure[cabinet_id] = {
                    "name": cabinet_name,
                    "workspaces": {}
                }

                # Get workspaces
                workspaces = self.api.list_workspaces(cabinet_id)
                for workspace in workspaces:
                    workspace_id = workspace.get("id")
                    workspace_name = workspace.get("name", f"Workspace {workspace_id}")

                    structure[cabinet_id]["workspaces"][workspace_id] = {
                        "name": workspace_name,
                        "folders": {}
                    }

                    # Get folders (limit to avoid too many API calls)
                    try:
                        folders = self.api.list_folders(workspace_id)
                        for folder in folders[:10]:  # Limit to first 10 folders
                            folder_id = folder.get("id")
                            folder_name = folder.get("name", f"Folder {folder_id}")

                            structure[cabinet_id]["workspaces"][workspace_id]["folders"][folder_id] = {
                                "name": folder_name
                            }
                    except Exception as e:
                        self.log_sync_activity(f"Error getting folders for workspace {workspace_name}: {e}", "WARNING")

            return structure

        except Exception as e:
            error_msg = f"Error getting cabinet structure: {str(e)}"
            self.log_sync_activity(error_msg, "ERROR")
            return {}

    def sync_folder(self, folder_id: str) -> Dict[str, Any]:
        """Sync all documents in a specific folder"""
        try:
            self.log_sync_activity(f"Syncing folder: {folder_id}")

            # Get documents in folder
            documents = self.api.get_folder_documents(folder_id)

            return self.sync_documents(documents)

        except Exception as e:
            error_msg = f"Error syncing folder {folder_id}: {str(e)}"
            self.log_sync_activity(error_msg, "ERROR")
            return {
                "success": False,
                "error": error_msg,
                "synced_count": 0,
                "failed_count": 0
            }

    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get statistics about synced documents"""
        sync_state = self.get_sync_state()

        return {
            "last_sync": sync_state.get("last_sync"),
            "total_synced": len(sync_state.get("synced_documents", {})),
            "failed_documents": len(sync_state.get("failed_documents", [])),
            "connection_status": self.api.get_connection_status()
        }