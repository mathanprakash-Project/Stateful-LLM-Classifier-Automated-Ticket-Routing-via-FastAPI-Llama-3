"""
FastAPI application entry point for AI-Powered Support Ticket Management System.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.api.routes import (
    auth_router,
    ticket_router,
    chat_router,
    dashboard_router,
    category_router,
    user_router,
    event_router,
)
from app.config.settings import settings
from app.core.error_handlers import register_error_handlers
from app.db.seed import run_seed
from app.middleware import RequestIdMiddleware, LoggingMiddleware

# Legacy classifier imports for backward-compatible endpoint
from app.graph import run_pipeline
from app.modules.prompt_versioning import list_versions, get_active_version
from app.modules.cost_calculator import session_tracker

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App Lifespan: DB initialization & Seeding
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database and seed data...")
    try:
        await run_seed()
        logger.info("Database ready.")
    except Exception as exc:
        logger.error("Failed to run seed: %s", exc)

    yield
    summary = session_tracker.summary
    logger.info("Application shutdown. Total LLM cost: $%.6f over %d calls", summary["total_cost_usd"], summary["calls"])


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Support Ticket Management System with LangGraph Agent, RBAC, and Real-time Dashboard",
    version="2.0.0",
    lifespan=lifespan,
)

# Register Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# Register Error Handlers
register_error_handlers(app)

# Include API Routers
app.include_router(auth_router)
app.include_router(ticket_router)
app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(category_router)
app.include_router(user_router)
app.include_router(event_router)


# ---------------------------------------------------------------------------
# Health Check & Legacy Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": "2.0.0"}


class ClassifyRequest(BaseModel):
    ticket_text: str = Field(..., min_length=5, max_length=4000)
    channel: str = Field(default="web_form", pattern="^(web_form|email)$")


class ClassifyResponse(BaseModel):
    issue_category: str
    assigned_team: str
    priority: str
    user_sentiment: str
    confidence_score: float
    reasoning: str
    requires_human_review: bool
    pii_detected: bool
    prompt_version: str | None
    cost_info: dict | None
    injection_blocked: bool


@app.get("/prompts")
async def get_prompts():
    return {"versions": list_versions(), "active": get_active_version()}


@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    try:
        state = run_pipeline(request.ticket_text, request.channel)
    except Exception as exc:
        logger.exception("Pipeline error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    classification = state.get("classification")
    if classification is None:
        raise HTTPException(status_code=422, detail=state.get("error", "Classification failed"))

    return ClassifyResponse(
        issue_category=classification.issue_category.value,
        assigned_team=classification.assigned_team.value,
        priority=classification.priority.value,
        user_sentiment=classification.user_sentiment.value,
        confidence_score=classification.confidence_score,
        reasoning=classification.reasoning,
        requires_human_review=classification.requires_human_review,
        pii_detected=state.get("pii_detected", False),
        prompt_version=state.get("prompt_version"),
        cost_info=state.get("cost_info"),
        injection_blocked=state.get("injection_blocked", False),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
