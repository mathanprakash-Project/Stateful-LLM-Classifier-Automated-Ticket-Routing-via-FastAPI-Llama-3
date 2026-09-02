"""
Ticket schemas for creation, update, filtering, and detail responses.
"""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.auth import UserSummary
from app.schemas.category import CategoryResponse, SubcategoryResponse


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    category_id: str
    subcategory_id: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    meta_info: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None
    activity_code: str | None = None
    technical_scope: str | None = None
    operation_status: str | None = None
    responsible_team: str | None = None
    requires_admin_approval: bool = False
    execution_mode: str | None = "Online"
    downtime_required: bool = False
    downtime_acknowledged: bool = False
    prerequisites_confirmed: bool = False
    prerequisites_notes: str | None = None


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    status: Optional[str] = Field(None, pattern="^(draft|open|assigned|in_progress|escalated|resolved|closed|reopened|cancelled|pending_manager_routing|pending_admin_approval|approved|rejected|routed)$")
    assigned_to_id: Optional[str] = None
    comment: Optional[str] = None
    change_reason: Optional[str] = None
    version: Optional[int] = None
    operation_status: Optional[str] = None
    prerequisites_notes: Optional[str] = None


class ReopenRequest(BaseModel):
    reason: str = Field(default="", max_length=2000)


class TicketCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    is_internal: bool = False


class TicketCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    user_id: str
    author: Optional[UserSummary] = None
    content: str
    is_internal: bool
    created_at: datetime


class TicketHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    changed_by_id: Optional[str] = None
    changed_by: Optional[UserSummary] = None
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: datetime


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_number: str
    title: str
    description: str
    priority: str
    status: str
    meta_info: dict[str, Any] = {}
    version: int
    created_by_id: str
    creator: Optional[UserSummary] = None
    assigned_to_id: Optional[str] = None
    assignee: Optional[UserSummary] = None
    category_id: str
    category: Optional[CategoryResponse] = None
    subcategory_id: Optional[str] = None
    subcategory: Optional[SubcategoryResponse] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    comments: List[TicketCommentResponse] = []
    history: List[TicketHistoryResponse] = []
    activity_code: str | None = None
    technical_scope: str | None = None
    operation_status: str | None = None
    responsible_team: str | None = None
    requires_admin_approval: bool = False
    routed_to_team: str | None = None
    execution_mode: str | None = None
    downtime_required: bool = False
    downtime_acknowledged: bool = False
    prerequisites_confirmed: bool = False
    prerequisites_notes: str | None = None


class TicketListSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_number: str
    title: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    category_name: Optional[str] = None
    creator_name: Optional[str] = None
    assignee_name: Optional[str] = None
    activity_code: str | None = None
    operation_status: str | None = None
    requires_admin_approval: bool = False
    execution_mode: str | None = None
    downtime_required: bool = False


class TicketListResponse(BaseModel):
    items: List[TicketListSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
