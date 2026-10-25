# Company Handbook Intelligence AI (Enterprise Edition v2.0)

An AI-powered Enterprise Company Handbook RAG Chatbot that answers employee policy questions using PDF documents, semantic search, hybrid retrieval, ChromaDB, and a locally hosted LLM. Built with React, FastAPI, Sentence Transformers, and SQLite, featuring page-accurate source citations, chat history, authentication, and role-based access control from the **Atos India Employee Policy Handbook v10.3**.

---

## 🌟 Key Capabilities & 11 Reference Screens

1. **Screen 1 — Split-Screen Login & Authentication**:
   - Left dark graphic panel with key feature highlights and security badges.
   - Right sign-in form with 1-click **Admin** and **Employee** demo access, email/password validation, remember me, and company SSO button.
2. **Screen 2 — AI Chat Main Interface**:
   - Fixed dark navigation sidebar (`#171717`) with logo, "+ New Chat" button, navigation links, and bottom user profile card.
   - Main chat workspace with welcome hero state, 4 recommended policy prompt cards, and bottom input pill.
3. **Screen 3 — Chat with Grounded Citations & Preview Modal**:
   - Numbered heading responses (`1. **Annual Leave Policy:**`, `2. **Maximum Privilege Leave Carry-Forward:**`, `3. **Work-from-Home Policy:**`).
   - Interactive red citation pills (`PDF Page 49`, `PDF Page 50`, `PDF Page 70`) that open the **Citation Grounding Preview Modal** displaying the exact excerpt indexed from the handbook.
4. **Screen 4 — Chat History Management**:
   - Searchable conversation table with checkboxes, conversation titles, last inquiry previews, timestamps, inline title renaming, and deletion.
5. **Screen 5 — Documents & Knowledge Base**:
   - 4 Stat Metric Cards: **Total Documents**, **Indexed & Searchable**, **Processing**, and **Failed**.
   - Drag-and-drop PDF upload modal that chunks and indexes new PDFs into persistent ChromaDB without clearing existing collections.
   - Document table with file size, chunk counts, status pills, download original PDF, and ChromaDB delete synchronization.
6. **Screen 6 — Settings & Preferences**:
   - Vertical sub-navigation tabs: **Profile**, **Security**, **Chat Preferences**, **Notifications**, **Appearance**, **Application**, and **Privacy**.
   - Real profile updates and password changes persisted to the database.
7. **Screen 7 — Admin Dashboard**:
   - Real-time platform metrics: Total Users, Total Documents, Total Conversations, and System Uptime.
   - 7-day conversation volume interactive bar chart.
   - Top most frequent employee questions with query counts and last asked timestamps.
   - User governance table with role switching (promote to Admin / demote to Employee).
8. **Screen 8 — Help & FAQ**:
   - Tabbed view: **Frequently Asked Questions** (interactive accordions with 1-click "Ask AI in Chat" buttons) and **User Guide & Best Practices**.
9. **Screen 9 — Feedback & Rating**:
   - Interactive 1–5 star rating with hover states, category selection, detailed comments, and database persistence.
10. **Screen 10 — Responsive Mobile View**:
    - Mobile header with hamburger menu button, sliding drawer sidebar, and responsive chat viewport.
11. **Screen 11 — User Profile Popover Dropdown**:
    - Clicking the user profile at the bottom of the sidebar reveals the popover menu with links to Profile, Settings, Help & FAQ, Feedback, and Sign Out.

---

## 🔐 Default Demo Accounts

| Role | Email | Password |
|---|---|---|
| **Administrator** | `admin@company.com` | `Admin@12345` |
| **Employee** | `abhishek@company.com` | `Abhishek@123` |

*Or click the 1-click demo buttons on the login screen to auto-fill credentials.*

---

## 🛠️ Tech Stack & Architecture

- **Backend**: FastAPI, SQLite (`data/handbook_ai.db`) with WAL mode, PyJWT token authentication, bcrypt password hashing.
- **RAG & Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`), ChromaDB persistent vector database (`data/chroma_db`).
- **Generation Engine**: Local Qwen LLM with strict grounded generation guardrails.
- **Frontend**: React 18, Vite, Lucide Icons, Vanilla CSS with custom Orange/White/Black SaaS design system.

---

---

## 🚀 Quickstart & Fresh Clone Setup

### 1. Prerequisites
- Python 3.10+ (Recommended: Python 3.11 or 3.12/3.13)
- Node.js 18+ and npm
- Git

### 2. Backend Setup
```bash
# 1. Clone repository
git clone https://github.com/your-org/company-handbook-ai.git
cd "company-handbook-ai"

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
# Copy the example environment file and set a secure JWT_SECRET_KEY
cp .env.example .env
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 4. Running the Application
```bash
# Terminal 1 — Start FastAPI Backend Server
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
# Health Endpoint: http://127.0.0.1:8000/health
# Swagger API Docs: http://127.0.0.1:8000/docs

# Terminal 2 — Start React + Vite Frontend
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
# Application URL: http://127.0.0.1:5173/
```

### 5. Automatic Resource Recreation & Seeding
- **SQLite Database (`data/handbook_ai.db`)**: Automatically created and schema-migrated on first backend startup. Default Administrator (`admin@company.com`) and Employee (`abhishek@company.com`) accounts are auto-seeded.
- **Storage Directories**: `data/documents/` and `data/chroma_db/` are automatically initialized if missing.
- **Document Indexing**: Upload any company handbook or policy PDF through the web UI under **Documents & Knowledge Base** or via `POST /api/upload`. Chunks and embeddings are automatically indexed into persistent ChromaDB.

### 6. Automated Verification & Testing
```bash
# Run complete test suite (53 unit, security, and RAG regression tests)
pytest tests/ -v

# Run production end-to-end workflow test
pytest tests/test_e2e_workflow.py -v -s

# Build frontend production bundle
cd frontend && npm run build
```

