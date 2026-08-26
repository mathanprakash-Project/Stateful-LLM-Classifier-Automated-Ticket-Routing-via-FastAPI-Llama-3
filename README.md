# AI-Powered Support Ticket Classifier

An intelligent support ticket triage, classification, and routing system built with LangGraph, FastAPI, and local Ollama models.

## Project Structure

```
LLM Project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & REST endpoints
│   │   ├── graph.py             # LangGraph state machine & pipeline
│   │   ├── schema.py            # Pydantic schemas and enums
│   │   └── modules/             # Pipeline components (PII, Injection guard, etc.)
│   ├── tests/
│   │   └── test_classifier.py  # Pytest test suite
│   ├── .env                     # Environment configuration
│   ├── .env.example             # Example environment configuration
│   ├── requirements.txt         # Backend Python dependencies
│   └── Dockerfile               # Backend Docker configuration
├── frontend/
│   ├── index.html               # Single-page web interface
│   └── Dockerfile               # Frontend Nginx Docker configuration
└── README.md
```

## Running the Application

### 1. Backend Setup (Local Python)

Navigate to the `backend/` directory:

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

Start the FastAPI backend server:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be live at `http://localhost:8000`.

### 2. Running Tests

From the project root or inside `backend/`:

```bash
pytest backend/tests/test_classifier.py -v
```

### 3. Frontend Setup (Local Web Browser)

Open `frontend/index.html` in any modern web browser or serve it via a static file server. It communicates with the backend running on `http://localhost:8000`.

---

## Docker Setup

When running inside a Docker container, `localhost` points inside the container itself. To connect to **Ollama** running on your host machine, `OLLAMA_BASE_URL` is set to `http://host.docker.internal:11434`.

### Backend Container

1. Build the backend image:
   ```bash
   docker build -t ticket-classifier-backend ./backend
   ```

2. Run the backend container:
   ```bash
   docker run -d --name classifier-backend -p 8000:8000 ticket-classifier-backend
   ```

*(Note: On Linux without Docker Desktop, add `--add-host=host.docker.internal:host-gateway` to your `docker run` command).*

### Frontend Container

1. Build the frontend image:
   ```bash
   docker build -t ticket-classifier-frontend ./frontend
   ```

2. Run the frontend container:
   ```bash
   docker run -d --name classifier-frontend -p 80:80 ticket-classifier-frontend
   ```
