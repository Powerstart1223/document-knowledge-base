# Workflow Architecture — Visual Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         LOGIN / REGISTER                        │
│                  (Secure authentication with bcrypt)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LANDING PAGE                               │
│                                                                 │
│   ┌──────────────────────┐       ┌──────────────────────┐     │
│   │  📝 Edit Existing    │       │  ✨ Create New       │     │
│   │     Document         │       │     Document         │     │
│   │                      │       │                      │     │
│   │  Upload & modify     │       │  Generate from       │     │
│   │  with AI assistance  │       │  scratch with AI     │     │
│   │                      │       │                      │     │
│   │  [Select]            │       │  [Select]            │     │
│   └──────────────────────┘       └──────────────────────┘     │
│                                                                 │
│   Sidebar: User Info | ⚙️ Settings | Sign Out | Status         │
└────────┬─────────────────────────────────────┬─────────────────┘
         │                                     │
         │                                     │
┌────────▼──────────────────┐   ┌─────────────▼──────────────────┐
│   PATH A: EDIT EXISTING   │   │   PATH B: CREATE NEW           │
└───────────────────────────┘   └────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
PATH A: EDIT EXISTING DOCUMENT
═══════════════════════════════════════════════════════════════════

Step 1: Upload
┌─────────────────────────────────────────────────────────────────┐
│  📄 Upload Your Document                                        │
│                                                                 │
│  [Choose file] (PDF, DOCX, TXT)                                │
│                                                                 │
│  ✅ Loaded 5,432 characters from contract.pdf                  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
Step 2+: Preview & AI-Assisted Editing
┌─────────────────────────────────────────────────────────────────┐
│  Document: contract.pdf | Length: 5,432 chars | Version: 3     │
├───────────────────────────────────────┬─────────────────────────┤
│  📄 DOCUMENT PREVIEW & EDIT           │  🤖 AI ASSISTANT        │
│  ┌─────────────────────────────────┐  │  ┌───────────────────┐ │
│  │ [Editable text area]            │  │  │ Chat History:     │ │
│  │                                 │  │  │                   │ │
│  │ CONTRACT AGREEMENT              │  │  │ User: Make this   │ │
│  │ This agreement is entered...    │  │  │ more formal       │ │
│  │                                 │  │  │                   │ │
│  │ Party A: ABC Corp               │  │  │ AI: ✅ Changes    │ │
│  │ Party B: XYZ LLC                │  │  │ applied!          │ │
│  │ ...                             │  │  │                   │ │
│  │                                 │  │  └───────────────────┘ │
│  └─────────────────────────────────┘  │                        │
│                                        │  [Chat input: "Add a   │
│  [↶ Undo] [⬇️ Download .docx] [🔄]    │   confidentiality..."]│
│                                        │                        │
│  📜 Version History                    │                        │
│   v0: Original document                │                        │
│   v1: Made more formal                 │                        │
│   v2: Added confidentiality clause     │                        │
│                                        │                        │
└────────────────────────────────────────┴────────────────────────┘
         │
         ▼
    Download edited document as .docx
    [← Back to Home]


═══════════════════════════════════════════════════════════════════
PATH B: CREATE NEW DOCUMENT
═══════════════════════════════════════════════════════════════════

Step 1: Document Type Selection
┌─────────────────────────────────────────────────────────────────┐
│  ✨ Create a New Document                                       │
│                                                                 │
│  Select Document Type:                                          │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                        │
│  │  📜     │  │  🤝     │  │  🔒     │                        │
│  │Contract │  │Indep.   │  │  NDA    │                        │
│  │Agreement│  │Contr.   │  │  /      │                        │
│  │         │  │Agrmt.   │  │Confid.  │                        │
│  │[Select] │  │[Select] │  │[Select] │                        │
│  └─────────┘  └─────────┘  └─────────┘                        │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                        │
│  │  💼     │  │  🏢     │  │  📋     │                        │
│  │Employ.  │  │Operating│  │ Legal   │                        │
│  │Agrmt.   │  │Agrmt/LLC│  │  Memo   │                        │
│  │         │  │         │  │         │                        │
│  │[Select] │  │[Select] │  │[Select] │                        │
│  └─────────┘  └─────────┘  └─────────┘                        │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                        │
│  │  ⚖️     │  │  📑     │  │  ✉️     │                        │
│  │  Brief  │  │Corporate│  │ Letter  │                        │
│  │ /Motion │  │ Filing  │  │  /      │                        │
│  │         │  │         │  │Corresp. │                        │
│  │[Select] │  │[Select] │  │[Select] │                        │
│  └─────────┘  └─────────┘  └─────────┘                        │
│                                                                 │
│                    ┌─────────┐                                 │
│                    │  ✏️     │                                 │
│                    │ Custom  │                                 │
│                    │Document │                                 │
│                    │         │                                 │
│                    │[Select] │                                 │
│                    └─────────┘                                 │
└─────────────────────────────────────────────────────────────────┘
                             │
                 (User selects "Independent Contractor Agreement")
                             │
                             ▼
              AI generates required fields dynamically
                             │
                             ▼
Step 2: Dynamic Form
┌─────────────────────────────────────────────────────────────────┐
│  Document Type: Independent Contractor Agreement                │
│                                                                 │
│  📋 Document Information                                        │
│                                                                 │
│  Company Name:          [ABC Corp                           ]  │
│  Contractor Name:       [John Doe                           ]  │
│  Contractor Address:    [123 Main St, City, State          ]  │
│  Services Description:  [Software development services...   ]  │
│  Compensation Amount:   [$5,000                             ]  │
│  Payment Terms:         [Net 30 days, monthly invoicing... ]  │
│  Start Date:            [2024-01-15                         ]  │
│  End Date:              [2024-12-15                         ]  │
│  IP Assignment:         [Yes                                ]  │
│  Confidentiality Req.:  [NDA required, 2-year term...       ]  │
│  Governing Law:         [State of California                ]  │
│  Termination Notice:    [30 days                            ]  │
│                                                                 │
│  [✨ Generate Document]                                         │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    LLM generates document
                             │
                             ▼
Step 3: Preview & AI-Assisted Editing
┌─────────────────────────────────────────────────────────────────┐
│  Document Type: Independent Contractor Agreement                │
├───────────────────────────────────────┬─────────────────────────┤
│  📄 DOCUMENT PREVIEW & EDIT           │  🤖 AI ASSISTANT        │
│  ┌─────────────────────────────────┐  │  ┌───────────────────┐ │
│  │ [Editable text area]            │  │  │ Request revisions:│ │
│  │                                 │  │  │                   │ │
│  │ INDEPENDENT CONTRACTOR AGREEMENT│  │  │ "Add a non-      │ │
│  │                                 │  │  │  compete clause" │ │
│  │ This Agreement is made...       │  │  │                   │ │
│  │                                 │  │  │ "Make payment    │ │
│  │ 1. SERVICES                     │  │  │  terms clearer"  │ │
│  │ Contractor shall provide...     │  │  │                   │ │
│  │                                 │  │  │ "Change tone to  │ │
│  │ 2. COMPENSATION                 │  │  │  more formal"    │ │
│  │ ...                             │  │  │                   │ │
│  │                                 │  │  └───────────────────┘ │
│  └─────────────────────────────────┘  │                        │
│                                        │  [Chat input box]      │
│  [🔄 Start Over] [⬇️ Download .docx]  │                        │
└────────────────────────────────────────┴────────────────────────┘
         │
         ▼
    Download generated document as .docx
    [← Back to Home]


═══════════════════════════════════════════════════════════════════
SETTINGS (Accessible from Sidebar)
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  [← Back]                                                       │
│                                                                 │
│  ⚙️ Settings                                                    │
│                                                                 │
│  [🤖 LLM Provider] [👤 Profile] [👥 Admin]                     │
│                                                                 │
│  Current Settings:                                              │
│  Provider: Ollama (llama3.1:8b)                                │
│  Status: ✅ Connected                                           │
│                                                                 │
│  Select AI Provider:                                            │
│  ( ) 🏠 Ollama (Free, runs locally)                            │
│  (•) ☁️ OpenAI (Cloud-based, paid API)                         │
│                                                                 │
│  OpenAI Configuration:                                          │
│  API Key: [sk-proj-****************************]               │
│  Model:   [gpt-4o-mini ▼]                                      │
│                                                                 │
│  [💾 Save Settings]                                             │
└─────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
SIDEBAR (Always Visible)
═══════════════════════════════════════════════════════════════════

┌─────────────────────┐
│ John Smith          │
│ john@lawfirm.com    │
│ ADMIN               │
│                     │
│ [Sign Out]          │
├─────────────────────┤
│ ⚙️ Quick Access     │
│                     │
│ [⚙️ Settings]       │
├─────────────────────┤
│ 🔌 Status           │
│                     │
│ ✅ Ollama           │
│   (llama3.1:8b)     │
└─────────────────────┘


═══════════════════════════════════════════════════════════════════
KEY FEATURES
═══════════════════════════════════════════════════════════════════

✅ Two-path workflow (Edit vs. Create)
✅ AI chat assistant in both workflows
✅ Version history with undo (Edit path)
✅ Dynamic field generation based on document type
✅ 10 document types with comprehensive field templates
✅ Editable document preview
✅ Professional .docx export
✅ Clean, modern UI with elegant cards
✅ Mobile responsive
✅ Settings accessible via sidebar
✅ Back navigation throughout
✅ Clear status indicators
```
