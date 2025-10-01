"""
NetDocuments Integration Module
Provides integration with NetDocuments cloud storage for document retrieval
"""

import os
import json
import requests
import tempfile
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, parse_qs, urlparse
import webbrowser
import time
from pathlib import Path

from config import Config

class NetDocumentsAPI:
    """NetDocuments API client for document retrieval"""

    def __init__(self, config_file: str = ".netdocuments_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.access_token = None
        self.base_url = None

        # API endpoints
        self.auth_url = "https://vault.netvoyage.com/neWeb2/OAuth.aspx"
        self.token_url = "https://api.vault.netvoyage.com/v1/oauth/access_token"

    def _load_config(self) -> Dict[str, Any]:
        """Load NetDocuments configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save NetDocuments configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def setup_credentials(self, client_id: str, client_secret: str,
                         redirect_uri: str = "https://localhost:3000/gettoken"):
        """Set up NetDocuments API credentials"""
        self.config.update({
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "scope": "read lookup"  # Read and lookup permissions
        })
        self._save_config()

    def get_authorization_url(self) -> str:
        """Generate authorization URL for OAuth flow"""
        if not self.config.get("client_id"):
            raise ValueError("Client ID not configured. Run setup_credentials() first.")

        params = {
            "response_type": "code",
            "client_id": self.config["client_id"],
            "redirect_uri": self.config["redirect_uri"],
            "scope": self.config["scope"]
        }

        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, authorization_code: str) -> bool:
        """Exchange authorization code for access token"""
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": self.config["client_id"],
            "client_secret": self.config["client_secret"],
            "redirect_uri": self.config["redirect_uri"]
        }

        try:
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")
            self.base_url = token_data.get("base_uri", "https://api.vault.netvoyage.com")

            # Save tokens to config
            self.config.update({
                "access_token": self.access_token,
                "base_url": self.base_url,
                "refresh_token": token_data.get("refresh_token"),
                "token_expires": int(time.time()) + token_data.get("expires_in", 3600)
            })
            self._save_config()

            return True

        except requests.RequestException as e:
            print(f"Error exchanging code for token: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        if not self.access_token:
            self.access_token = self.config.get("access_token")

        if not self.access_token:
            raise ValueError("Not authenticated. Complete OAuth flow first.")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, endpoint: str, method: str = "GET",
                     params: Optional[Dict] = None, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to NetDocuments API"""
        if not self.base_url:
            self.base_url = self.config.get("base_url", "https://api.vault.netvoyage.com")

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def get_user_info(self) -> Optional[Dict]:
        """Get current user information"""
        return self._make_request("/v1/user")

    def get_cabinets(self) -> List[Dict]:
        """Get list of accessible cabinets"""
        result = self._make_request("/v1/cabinets")
        return result.get("items", []) if result else []

    def search_documents(self, query: str, cabinet_id: Optional[str] = None,
                        max_results: int = 100) -> List[Dict]:
        """Search for documents in NetDocuments"""
        search_params = {
            "q": query,
            "max": max_results,
            "searchType": "fulltext"
        }

        if cabinet_id:
            search_params["cabinet"] = cabinet_id

        endpoint = "/v1/search"
        result = self._make_request(endpoint, params=search_params)

        return result.get("items", []) if result else []

    def get_document_info(self, document_id: str) -> Optional[Dict]:
        """Get detailed information about a specific document"""
        return self._make_request(f"/v1/documents/{document_id}")

    def download_document(self, document_id: str, save_path: Optional[str] = None) -> Optional[str]:
        """Download a document and return the local file path"""
        if not self.access_token:
            self.access_token = self.config.get("access_token")

        if not self.access_token:
            raise ValueError("Not authenticated. Complete OAuth flow first.")

        # Get document info first
        doc_info = self.get_document_info(document_id)
        if not doc_info:
            return None

        # Construct download URL
        download_url = f"{self.base_url}/v1/documents/{document_id}/content"

        try:
            response = requests.get(download_url, headers=self._get_headers(), stream=True)
            response.raise_for_status()

            # Determine filename
            filename = doc_info.get("name", f"document_{document_id}")
            if not save_path:
                # Create temporary file
                suffix = Path(filename).suffix if '.' in filename else '.tmp'
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    save_path = tmp.name

            # Save file
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return save_path

        except requests.RequestException as e:
            print(f"Error downloading document {document_id}: {e}")
            return None

    def get_recent_documents(self, days: int = 30, max_results: int = 50) -> List[Dict]:
        """Get recently modified documents"""
        # NetDocuments search with date filter
        search_params = {
            "q": f"modified:[{days} days ago TO now]",
            "max": max_results,
            "sort": "modified",
            "order": "desc"
        }

        result = self._make_request("/v1/search", params=search_params)
        return result.get("items", []) if result else []

    def list_workspaces(self, cabinet_id: str) -> List[Dict]:
        """List workspaces in a cabinet"""
        result = self._make_request(f"/v1/cabinets/{cabinet_id}/workspaces")
        return result.get("items", []) if result else []

    def list_folders(self, workspace_id: str) -> List[Dict]:
        """List folders in a workspace"""
        result = self._make_request(f"/v1/workspaces/{workspace_id}/folders")
        return result.get("items", []) if result else []

    def get_folder_documents(self, folder_id: str) -> List[Dict]:
        """Get documents in a specific folder"""
        result = self._make_request(f"/v1/folders/{folder_id}/documents")
        return result.get("items", []) if result else []

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        if not self.access_token:
            self.access_token = self.config.get("access_token")

        if not self.access_token:
            return False

        # Check if token is expired
        token_expires = self.config.get("token_expires", 0)
        if time.time() >= token_expires:
            return False

        return True

    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status and user info"""
        if not self.is_authenticated():
            return {
                "connected": False,
                "error": "Not authenticated"
            }

        user_info = self.get_user_info()
        if user_info:
            return {
                "connected": True,
                "user": user_info.get("name", "Unknown"),
                "email": user_info.get("email", "Unknown"),
                "base_url": self.base_url
            }
        else:
            return {
                "connected": False,
                "error": "Failed to get user info"
            }