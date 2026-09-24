"""
API endpoints for SupportHub AI Model Monitoring & LLM Observability telemetry.
"""

from fastapi import APIRouter, Depends
from typing import Any, Dict

from app.api.dependencies import get_current_user
from app.models import User
from app.core.model_tracker import model_tracker

router = APIRouter(prefix="/metrics", tags=["Model Monitoring"])


@router.get("/model-monitoring")
async def get_model_monitoring_metrics() -> Dict[str, Any]:
    """
    Returns real-time model usage, cost router breakdown, token consumption,
    RAG retrieval metrics, Responsible AI compliance flags, and recent invocation telemetry.
    """
    return model_tracker.get_metrics_summary()
