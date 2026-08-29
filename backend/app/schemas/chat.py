"""
Chat and AI draft schemas.
"""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreate(BaseModel):
    pass


class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    content: str
    message_type: str
    metadata_info: dict[str, Any] = {}
    created_at: datetime


class TicketDraftData(BaseModel):
    title: str
    description: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    subcategory_id: Optional[str] = None
    subcategory_name: Optional[str] = None
    priority: str = "medium"
    meta_info: dict[str, Any] = {}


class DraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    user_id: str
    ticket_id: Optional[str] = None
    status: str
    draft_data: dict[str, Any]
    revision: int
    created_at: datetime
    updated_at: datetime


class DraftUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    subcategory_id: Optional[str] = None
    subcategory_name: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    meta_info: Optional[dict[str, Any]] = None


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: str
    created_at: datetime
    messages: List[ChatMessageResponse] = []
    drafts: List[DraftResponse] = []

