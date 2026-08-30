# SupportHub AI - Enterprise IT Support & Ticket Management System

An enterprise-grade, AI-powered IT support ticket management and triage platform built with **FastAPI**, **LangGraph multi-turn agents**, **Ollama**, **uv**, and a modern **Angular 22 Material Design 3** frontend.

---

## 🌟 Key Features

- 🤖 **LangGraph Multi-Turn Diagnostic Agent**:
  - **Conversational Triage**: Engages users in diagnostic dialogue (symptoms, hardware/OS version, impact, troubleshooting steps) before drafting tickets.
  - **Domain Guardrails & Out-of-Scope Filter**: Distinguishes valid IT/technical issues from personal/non-IT topics (e.g. clothing, food, jokes) and politely refuses ticket creation for non-technical requests.
  - **Resilient Multi-Model Fallback**: Configured for `gpt-oss:120b-cloud` with automatic, seamless fallback to local Ollama models (`llama3.2:3b`).
  - **Human-in-the-Loop Approval**: Generates interactive structured draft cards (`Approve & Create Ticket` / `Reject Draft`) requiring user confirmation.
- 🎨 **Angular 22 Material Design 3 UI**:
  - **Dark & Light Mode**: Instant theme switcher with persistent settings across sessions.
  - **Streaming Typewriter Effect**: Real-time character animation for AI responses with formatted Markdown rendering.
  - **Dashboard & Analytics**: 5 KPI metric cards (Total, Open, In Progress, Resolved, Closed) and live activity feed.
  - **Ticket Registry**: Live keyword search, status filters, priority chips, and detailed inspector modal.
  - **Role Switcher & Inspector Controls**: Live user switching (`User`, `Agent`, `Manager`, `Admin`) with workflow state transitions, assignee reassignment, audit timeline, and comment threads.
- ⚡ **Modern Stack & Lightning Package Management**:
  - Managed with **`uv`** for reproducible dependencies (`pyproject.toml` & `uv.lock`).
  - Real-time Server-Sent Events (**SSE**) for instant cross-client updates (`/api/events/stream`).
  - Strict Role-Based Access Control (**RBAC**) and audited state machine transitions.

---

## 📁 Project Structure

```
LLM Project/
├── backend/
│   ├── app/
│   │   ├── agents/                  # LangGraph stateful triage workflow & nodes
│   │   │   ├── nodes/               # Intent classification, info extraction, completeness check, draft generation
│   │   │   ├── prompts/             # System prompts and domain guardrails
│   │   │   ├── graph.py             # LangGraph StateGraph pipeline definition
│   │   │   └── state.py             # AgentState TypedDict schema
│   │   ├── api/
│   │   │   ├── routes/              # Auth, Tickets, Chat, Dashboard, Categories, SSE stream
│   │   │   └── dependencies.py      # Auth and database dependencies
│   │   ├── config/                  # App settings via Pydantic BaseSettings
│   │   ├── core/                    # Security, LLM client, exceptions, logging
│   │   ├── db/                      # Database engine, session, migrations, and seed data
│   │   ├── models/                  # SQLAlchemy ORM models (User, Ticket, Draft, History, Comment)
│   │   ├── repositories/            # Data access repository layer
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── services/                # Business logic services (Ticket, Chat, Auth, Dashboard)
│   │   └── main.py                  # FastAPI application entrypoint
│   ├── tests/                       # 24 automated unit & integration tests
│   ├── Dockerfile                   # Multi-stage Docker build with uv
│   ├── pyproject.toml               # Python project configuration & pytest settings
│   ├── uv.lock                      # Locked dependency tree
│   └── requirements.txt             # Exported dependencies
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   └── app.component.ts     # Standalone Angular 22 Component (Shell, Dashboard, Chat, Modals)
│   │   ├── styles.css               # Material 3 design tokens, themes, dropdown styling
│   │   ├── index.html               # Main HTML entrypoint
│   │   └── main.ts                  # Angular bootstrap
│   ├── angular.json                 # Angular CLI build configuration
│   ├── package.json                 # Node & Angular dependencies
│   ├── nginx.conf                   # Nginx reverse proxy (/api/ -> backend) & SPA routing
│   └── Dockerfile                   # Multi-stage build (Node 20 -> Nginx Alpine)
├── docker-compose.yml               # Multi-container orchestration (postgres, api, ui)
└── README.md
```

---

## 🚀 Quick Start with Docker Compose

Ensure [Docker Desktop](https://www.docker.com/) is installed and running.

1. **Launch all services**:
   ```bash
   docker compose up -d --build
   ```

2. **Access the applications**:
   - **Frontend UI**: [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

3. **Check container statuses**:
   ```bash
   docker compose ps
   ```

---

## 💻 Local Development Setup

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 20+** & **npm**
- **uv** (`pip install uv` or install via Astral installer)
- **Ollama** running locally on port `11434` (with `llama3.2:3b` or `gpt-oss:120b-cloud`)

### 2. Backend Setup with `uv`

```bash
# Navigate to backend
cd backend

# Create virtual environment and install dependencies using uv
uv venv
.\.venv\Scripts\activate      # On Windows (or source .venv/bin/activate on Linux/macOS)
uv pip install -r requirements.txt

# Start FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup with Angular

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```
*The development UI runs at `http://localhost:4200` and proxies API calls to `http://localhost:8000`.*

---

## 🧪 Running Automated Tests

Run the complete test suite (24 tests covering RBAC, ticket state machines, classification, PII redaction, prompt injection guards, and multi-turn chat):

```bash
# From backend directory
cd backend
pytest -v
```

---

## 👥 Demo User Accounts & Roles

The system comes pre-seeded with accounts for all roles (Default Password for all: `password123`):

| Name | Email | Role | Capabilities |
| :--- | :--- | :--- | :--- |
| **John Doe** | `john@company.com` | `user` | Report issues, chat with AI, approve drafts, view own tickets |
| **Jane Smith** | `jane@company.com` | `user` | Standard employee user |
| **Agent Bob** | `bob@company.com` | `agent` | Triage tickets, update status (`in_progress`, `resolved`), add comments |
| **Manager Alice** | `alice@company.com` | `manager` | Reassign tickets, escalate, review SLA metrics |
| **Admin Root** | `admin@company.com` | `admin` | Full system control, close/cancel tickets, oversee all operations |

*You can switch between any of these users instantly using the **User Role Switcher** dropdown in the top-right header of the UI.*

---

## 📡 API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT access token |
| `GET` | `/api/auth/me` | Retrieve profile of currently authenticated user |
| `GET` | `/api/tickets` | List and filter tickets (supports pagination, search, status filter) |
| `POST` | `/api/tickets` | Create a new support ticket manually |
| `GET` | `/api/tickets/{id}` | Inspect ticket details, audit timeline, and comment thread |
| `PATCH` | `/api/tickets/{id}` | Transition ticket status or reassign ticket |
| `POST` | `/api/tickets/{id}/comments` | Add a comment to a ticket thread |
| `POST` | `/api/chat/sessions` | Create a new AI triage chat session |
| `POST` | `/api/chat/sessions/{id}/messages` | Send message to AI agent (runs LangGraph triage turn) |
| `POST` | `/api/chat/sessions/{id}/drafts/{draft_id}/approve` | Approve draft card and convert to official ticket |
| `POST` | `/api/chat/sessions/{id}/drafts/{draft_id}/reject` | Reject draft and reset triage state |
| `GET` | `/api/dashboard/stats` | Retrieve KPI metrics and recent activity |
| `GET` | `/api/events/stream` | Server-Sent Events stream for live real-time updates |
| `GET` | `/health` | API health check endpoint |
