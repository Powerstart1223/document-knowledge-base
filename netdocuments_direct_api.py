#!/usr/bin/env python3
"""
NetDocuments Direct API Integration
Direct interface with NetDocuments REST API without frameworks
"""

import requests
import json
import base64
from urllib.parse import urlencode, parse_qs
import webbrowser
from datetime import datetime

class NetDocumentsDirectAPI:
    """Direct NetDocuments API client"""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "https://localhost:3000/gettoken"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.base_url = None

        # API endpoints
        self.auth_url = "https://vault.netvoyage.com/neWeb2/OAuth.aspx"
        self.token_url = "https://api.vault.netvoyage.com/v1/oauth/access_token"

    def get_authorization_url(self) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read lookup"
        }
        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, authorization_code: str) -> dict:
        """Exchange authorization code for access token"""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()}"
        }

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }

        response = requests.post(self.token_url, headers=headers, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.base_url = token_data.get("base_uri", "https://api.vault.netvoyage.com")

        return token_data

    def _make_request(self, endpoint: str, method: str = "GET", params: dict = None, data: dict = None) -> dict:
        """Make authenticated API request"""
        if not self.access_token:
            raise ValueError("Not authenticated. Get access token first.")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def get_user_info(self) -> dict:
        """Get current user information"""
        return self._make_request("/v1/user")

    def get_cabinets(self) -> list:
        """Get list of accessible cabinets"""
        result = self._make_request("/v1/cabinets")
        return result.get("items", [])

    def search_documents(self, query: str, cabinet_id: str = None, max_results: int = 100) -> list:
        """Search for documents"""
        params = {
            "q": query,
            "max": max_results,
            "searchType": "fulltext"
        }

        if cabinet_id:
            params["cabinet"] = cabinet_id

        result = self._make_request("/v1/search", params=params)
        return result.get("items", [])

    def get_document_info(self, document_id: str) -> dict:
        """Get document metadata"""
        return self._make_request(f"/v1/documents/{document_id}")

    def download_document(self, document_id: str, save_path: str = None) -> str:
        """Download document content"""
        if not self.access_token:
            raise ValueError("Not authenticated")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.base_url}/v1/documents/{document_id}/content"

        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        if not save_path:
            save_path = f"document_{document_id}.tmp"

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return save_path

    def get_workspaces(self, cabinet_id: str) -> list:
        """Get workspaces in a cabinet"""
        result = self._make_request(f"/v1/cabinets/{cabinet_id}/workspaces")
        return result.get("items", [])

    def get_folders(self, workspace_id: str) -> list:
        """Get folders in a workspace"""
        result = self._make_request(f"/v1/workspaces/{workspace_id}/folders")
        return result.get("items", [])

    def get_folder_documents(self, folder_id: str) -> list:
        """Get documents in a folder"""
        result = self._make_request(f"/v1/folders/{folder_id}/documents")
        return result.get("items", [])

# Example usage
def example_netdocuments_integration():
    """Example of how to use the NetDocuments API"""

    # Step 1: Initialize API client
    client_id = "your_client_id_here"
    client_secret = "your_client_secret_here"

    api = NetDocumentsDirectAPI(client_id, client_secret)

    # Step 2: Get authorization (manual process)
    auth_url = api.get_authorization_url()
    print(f"1. Go to this URL: {auth_url}")
    print("2. Authorize the application")
    print("3. Copy the authorization code from the redirect URL")

    authorization_code = input("Enter authorization code: ")

    # Step 3: Get access token
    token_data = api.exchange_code_for_token(authorization_code)
    print(f"Access token obtained: {token_data['access_token'][:20]}...")

    # Step 4: Use the API
    try:
        # Get user info
        user = api.get_user_info()
        print(f"Logged in as: {user.get('name', 'Unknown')}")

        # Get cabinets
        cabinets = api.get_cabinets()
        print(f"Found {len(cabinets)} cabinets")

        # Search documents
        if cabinets:
            cabinet_id = cabinets[0]["id"]
            documents = api.search_documents("contract", cabinet_id, max_results=5)
            print(f"Found {len(documents)} documents matching 'contract'")

            # Get details of first document
            if documents:
                doc = documents[0]
                doc_info = api.get_document_info(doc["id"])
                print(f"Document: {doc_info.get('name', 'Unknown')}")

                # Download document (optional)
                # file_path = api.download_document(doc["id"])
                # print(f"Downloaded to: {file_path}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    example_netdocuments_integration()