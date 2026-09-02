"""
Dashboard aggregation and metrics schemas.
"""

from typing import Any, List, Optional
from pydantic import BaseModel

from app.schemas.ticket import TicketListSummary


class StatusMetric(BaseModel):
    status: str
    count: int


class PriorityMetric(BaseModel):
    priority: str
    count: int


class CategoryMetric(BaseModel):
    category_name: str
    count: int


class DashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    assigned_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    escalated_tickets: int
    pending_routing_tickets: int = 0
    pending_approval_tickets: int = 0
    priority_distribution: List[PriorityMetric] = []
    category_distribution: List[CategoryMetric] = []
    recent_tickets: List[TicketListSummary] = []

