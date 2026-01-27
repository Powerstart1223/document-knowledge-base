# NetDocuments Direct Integration Setup

## 🔑 Step 1: Get API Credentials

### Access Developer Portal
1. **Log into NetDocuments** with admin account
2. **Go to Admin → Developer Portal**
3. **Click "Create New Application"**

### Application Setup
- **Application Name:** Your App Name
- **Application Type:** Web Application
- **Redirect URI:** `https://localhost:3000/gettoken`
- **Scopes:** Select `read`, `lookup`, `organize` (as needed)

### Get Credentials
- **Client ID:** Copy this value
- **Client Secret:** Copy this value (keep secure!)

## 🔐 Step 2: OAuth Authentication

### Method 1: Manual Browser Flow
```python
from netdocuments_direct_api import NetDocumentsDirectAPI

# Initialize
api = NetDocumentsDirectAPI("your_client_id", "your_client_secret")

# Get authorization URL
auth_url = api.get_authorization_url()
print(f"Go to: {auth_url}")

# User goes to URL, authorizes, gets code
code = input("Enter authorization code: ")

# Exchange for token
token_data = api.exchange_code_for_token(code)
print(f"Access Token: {token_data['access_token']}")
```

### Method 2: Using cURL
```bash
# Step 1: Get authorization code (manual browser step)
open "https://vault.netvoyage.com/neWeb2/OAuth.aspx?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://localhost:3000/gettoken&scope=read%20lookup"

# Step 2: Exchange code for token
curl -X POST https://api.vault.netvoyage.com/v1/oauth/access_token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic $(echo -n 'CLIENT_ID:CLIENT_SECRET' | base64)" \
  -d "grant_type=authorization_code&code=AUTH_CODE&redirect_uri=https://localhost:3000/gettoken"
```

## 📡 Step 3: API Usage

### Basic Operations
```python
# Initialize with token
client = SimpleNetDocsClient("your_access_token")

# Search documents
docs = client.search("contract")

# Download document
client.download_document(doc_id, "contract.pdf")

# Bulk export
client.export_search_results("agreement", "./exports")
```

### Advanced Operations
```python
from netdocuments_direct_api import NetDocumentsDirectAPI

api = NetDocumentsDirectAPI(client_id, client_secret)
# ... authenticate ...

# Get cabinets
cabinets = api.get_cabinets()

# Get workspaces
workspaces = api.get_workspaces(cabinet_id)

# Get folders
folders = api.get_folders(workspace_id)

# Get folder documents
docs = api.get_folder_documents(folder_id)
```

## 🔄 Step 4: Common Use Cases

### 1. Document Search and Download
```python
# Search for specific documents
results = client.search("software license agreement")

for doc in results:
    print(f"Found: {doc['name']}")
    client.download_document(doc['id'])
```

### 2. Bulk Document Export
```python
# Export all contracts
client.export_search_results("contract", "./contracts")

# Export by date range
client.export_search_results("modified:[2024-01-01 TO now]", "./recent_docs")
```

### 3. Workspace Exploration
```python
# Browse structure
cabinets = api.get_cabinets()
for cabinet in cabinets:
    workspaces = api.get_workspaces(cabinet['id'])
    for workspace in workspaces:
        folders = api.get_folders(workspace['id'])
        print(f"Cabinet: {cabinet['name']} → Workspace: {workspace['name']} → {len(folders)} folders")
```

## 🛠️ Step 5: Integration with Your Knowledge Base

### Method 1: Direct Integration
```python
# Download and process documents
docs = client.search("your_query")
for doc in docs:
    filepath = client.download_document(doc['id'])

    # Process with your existing system
    text = extract_text(filepath)
    add_to_knowledge_base(text, doc['name'])
```

### Method 2: Scheduled Sync
```python
import schedule
import time

def sync_netdocuments():
    # Get recent documents
    recent_docs = client.search("modified:[1 day ago TO now]")

    for doc in recent_docs:
        # Download and process
        process_document(doc)

# Run daily at 2 AM
schedule.every().day.at("02:00").do(sync_netdocuments)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

## 🔒 Security Considerations

### Token Management
- **Store tokens securely** (environment variables, key vault)
- **Refresh tokens** before expiration
- **Use HTTPS** for all communications
- **Limit token scope** to minimum required

### Access Control
- **Principle of least privilege**
- **Regular token rotation**
- **Monitor API usage**
- **Log access attempts**

## 📊 API Limits and Best Practices

### Rate Limits
- **Standard:** 1000 requests/hour
- **Burst:** 100 requests/minute
- **Implement retry logic** with exponential backoff

### Best Practices
- **Cache results** when possible
- **Use pagination** for large result sets
- **Implement error handling**
- **Monitor API usage**

### Error Handling
```python
import time
import random

def api_call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            raise
    raise Exception("Max retries exceeded")
```

## 🚀 Quick Start Script

Save this as `netdocs_quickstart.py`:
```python
#!/usr/bin/env python3
import os
from simple_netdocs_client import SimpleNetDocsClient

# Set your access token
ACCESS_TOKEN = os.getenv("NETDOCS_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("Set NETDOCS_ACCESS_TOKEN environment variable")
    exit(1)

client = SimpleNetDocsClient(ACCESS_TOKEN)

# Quick test
try:
    cabinets = client.list_cabinets()
    print(f"✅ Connected! Found {len(cabinets)} cabinets")

    # Search example
    docs = client.search("agreement", max_results=5)
    print(f"📄 Found {len(docs)} documents matching 'agreement'")

except Exception as e:
    print(f"❌ Error: {e}")
```

Run with:
```bash
export NETDOCS_ACCESS_TOKEN="your_token_here"
python netdocs_quickstart.py
```

## 📞 Support

- **API Documentation:** NetDocuments Developer Portal
- **Support:** Contact your NetDocuments administrator
- **Rate Limits:** Monitor in Developer Portal dashboard