# NetDocuments API - cURL Examples

## Authentication

### 1. Get Authorization Code
```bash
# Open this URL in browser
https://vault.netvoyage.com/neWeb2/OAuth.aspx?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://localhost:3000/gettoken&scope=read%20lookup
```

### 2. Exchange Code for Token
```bash
curl -X POST https://api.vault.netvoyage.com/v1/oauth/access_token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic $(echo -n 'CLIENT_ID:CLIENT_SECRET' | base64)" \
  -d "grant_type=authorization_code&code=YOUR_AUTH_CODE&redirect_uri=https://localhost:3000/gettoken"
```

## API Calls

### Get User Information
```bash
curl -X GET https://api.vault.netvoyage.com/v1/user \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

### List Cabinets
```bash
curl -X GET https://api.vault.netvoyage.com/v1/cabinets \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

### Search Documents
```bash
curl -X GET "https://api.vault.netvoyage.com/v1/search?q=contract&max=10&searchType=fulltext" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

### Get Document Details
```bash
curl -X GET https://api.vault.netvoyage.com/v1/documents/DOCUMENT_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

### Download Document
```bash
curl -X GET https://api.vault.netvoyage.com/v1/documents/DOCUMENT_ID/content \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o document.pdf
```

### List Workspaces
```bash
curl -X GET https://api.vault.netvoyage.com/v1/cabinets/CABINET_ID/workspaces \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

### List Folders
```bash
curl -X GET https://api.vault.netvoyage.com/v1/workspaces/WORKSPACE_ID/folders \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

### Get Folder Documents
```bash
curl -X GET https://api.vault.netvoyage.com/v1/folders/FOLDER_ID/documents \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

## Response Examples

### Cabinets Response
```json
{
  "items": [
    {
      "id": "12345",
      "name": "Legal Documents",
      "type": "Cabinet"
    }
  ]
}
```

### Search Response
```json
{
  "items": [
    {
      "id": "67890",
      "name": "Software License Agreement.docx",
      "modified": "2024-01-15T10:30:00Z",
      "author": "John Smith",
      "workspace": "Contracts"
    }
  ]
}
```

### Document Info Response
```json
{
  "id": "67890",
  "name": "Software License Agreement.docx",
  "extension": "docx",
  "size": 45678,
  "modified": "2024-01-15T10:30:00Z",
  "author": "John Smith",
  "workspace": "Contracts",
  "path": "/Legal Documents/Contracts/"
}
```