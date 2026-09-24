# 🐳 SupportHub AI — Docker Compose Operations

This directory contains scripts and configuration to run the entire SupportHub AI platform (PostgreSQL Database, FastAPI Backend, and Angular Frontend) with a single command or double-click.

---

## ⚡ Quick Start

### Option A: Double-Click (Windows)
- Double-click **`run.bat`** (or **`start.bat`**) to launch all services.
- Double-click **`stop.bat`** to stop all services.

### Option B: PowerShell
```powershell
# Start all services
.\start.ps1

# Stop all services
.\stop.ps1
```

### Option C: Docker Compose Command
```bash
# Launch in detached mode
docker compose up -d

# View live logs
docker compose logs -f

# Stop containers
docker compose down
```

---

## 🌐 Service URLs

| Service | URL | Description |
|:---|:---|:---|
| **Frontend UI** | [http://localhost:3000](http://localhost:3000) | Angular Web Application |
| **Ticket Status Tracker** | [http://localhost:3000/ticket-status](http://localhost:3000/ticket-status) | 5-stage customer tracker |
| **Backend API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger UI |
| **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | API & DB status |
| **PostgreSQL** | `localhost:5432` | Port exposed for inspection |

---

## 👥 Pre-Seeded Test Accounts

All accounts use the default password: **`password123`**

| Role | Name | Email |
|:---|:---|:---|
| **Customer / User** | Venu | `venu@company.com` |
| **Customer / User** | Kasi | `kasi@company.com` |
| **Support Agent** | Eegan | `eegan@company.com` |
| **Support Agent** | Hari | `hari@company.com` |
| **Manager** | Mathan | `mathan@company.com` |
| **Administrator** | Adhi | `adhi@company.com` |

---

## 🏗️ Architecture

- **`ticket_postgres`**: PostgreSQL 16 Alpine container with persistent named volume `pgdata`.
- **`ticket_api`**: FastAPI Python 3.11 container with LangGraph, SQLAlchemy, and hot-reload code mount (`../backend/app:/app/app`).
- **`ticket_ui`**: Production-built Angular 19 SPA served via Nginx with API reverse proxy.

