#!/usr/bin/env python3
"""
Simple NetDocuments Client
Minimal script to connect and extract documents from NetDocuments
"""

import requests
import json
import os
from datetime import datetime

class SimpleNetDocsClient:
    """Simplified NetDocuments client for basic operations"""

    def __init__(self, access_token: str, base_url: str = "https://api.vault.netvoyage.com"):
        self.access_token = access_token
        self.base_url = base_url

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Simple GET request"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{self.base_url}/{endpoint}", headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def _download(self, endpoint: str, save_path: str):
        """Download file"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{self.base_url}/{endpoint}", headers=headers, stream=True)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def search(self, query: str, max_results: int = 10) -> list:
        """Search documents"""
        params = {"q": query, "max": max_results, "searchType": "fulltext"}
        result = self._get("v1/search", params)
        return result.get("items", [])

    def get_document(self, doc_id: str) -> dict:
        """Get document information"""
        return self._get(f"v1/documents/{doc_id}")

    def download_document(self, doc_id: str, filename: str = None):
        """Download a document"""
        if not filename:
            doc_info = self.get_document(doc_id)
            filename = doc_info.get("name", f"document_{doc_id}")

        self._download(f"v1/documents/{doc_id}/content", filename)
        return filename

    def list_cabinets(self) -> list:
        """List accessible cabinets"""
        result = self._get("v1/cabinets")
        return result.get("items", [])

    def export_search_results(self, query: str, output_dir: str = "./netdocs_export"):
        """Export search results to local files"""
        os.makedirs(output_dir, exist_ok=True)

        print(f"Searching for: {query}")
        documents = self.search(query, max_results=50)

        print(f"Found {len(documents)} documents")

        for i, doc in enumerate(documents, 1):
            try:
                doc_id = doc["id"]
                doc_name = doc.get("name", f"document_{doc_id}")

                print(f"[{i}/{len(documents)}] Downloading: {doc_name}")

                # Create safe filename
                safe_filename = "".join(c for c in doc_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                filepath = os.path.join(output_dir, safe_filename)

                self.download_document(doc_id, filepath)

                # Save metadata
                metadata_file = filepath + ".json"
                with open(metadata_file, 'w') as f:
                    json.dump(doc, f, indent=2)

            except Exception as e:
                print(f"Error downloading {doc.get('name', 'unknown')}: {e}")

        print(f"Export completed. Files saved to: {output_dir}")

# Usage examples
def main():
    """Example usage"""
    # You need to get this token through OAuth first
    ACCESS_TOKEN = "your_access_token_here"

    client = SimpleNetDocsClient(ACCESS_TOKEN)

    try:
        # List cabinets
        print("=== Cabinets ===")
        cabinets = client.list_cabinets()
        for cabinet in cabinets:
            print(f"- {cabinet['name']} (ID: {cabinet['id']})")

        # Search for documents
        print("\n=== Search Results ===")
        query = "contract"
        documents = client.search(query)

        for doc in documents[:5]:  # Show first 5
            print(f"- {doc['name']} (Modified: {doc.get('modified', 'Unknown')})")

        # Download a specific document
        if documents:
            doc_id = documents[0]["id"]
            filename = client.download_document(doc_id)
            print(f"\nDownloaded: {filename}")

        # Bulk export
        print("\n=== Bulk Export ===")
        client.export_search_results("agreement", "./my_agreements")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()