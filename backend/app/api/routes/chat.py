"""
Chat routes: session management, AI conversation, and draft review.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
    DraftResponse,
    DraftUpdateRequest,
)
from app.schemas.common import SuccessMessageResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat & AI Agent"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    return await chat_service.create_session(current_user)


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    return await chat_service.list_user_sessions(current_user)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_service = ChatService(db)
    return await chat_service.get_session(session_id, current_user)


@router.post("/sessions/{session_id}/messages")
async def send_chat_message(
    session_id: str,
    msg_in: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_service = ChatService(db)
    result = await chat_service.process_user_message(session_id, current_user, msg_in.content)
    draft_resp = None
    if result.get("draft"):
        draft = result["draft"]
        draft_resp = {
            "id": draft.id,
            "session_id": draft.session_id,
            "user_id": draft.user_id,
            "ticket_id": draft.ticket_id,
            "status": draft.status,
            "draft_data": draft.draft_data,
            "revision": draft.revision,
            "created_at": draft.created_at,
            "updated_at": draft.updated_at,
        }

    return {
        "response": result["response_text"],
        "draft": draft_resp,
        "needs_human_approval": result["needs_human_approval"],
    }


@router.post("/sessions/{session_id}/drafts/{draft_id}/approve")
async def approve_draft(
    session_id: str,
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_service = ChatService(db)
    return await chat_service.approve_draft(session_id, draft_id, current_user)


@router.patch("/sessions/{session_id}/drafts/{draft_id}", response_model=DraftResponse)
async def update_draft(
    session_id: str,
    draft_id: str,
    updates: DraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_service = ChatService(db)
    return await chat_service.update_draft(
        session_id, draft_id, current_user, updates.model_dump(exclude_unset=True)
    )


@router.post("/sessions/{session_id}/drafts/{draft_id}/reject", response_model=SuccessMessageResponse)
async def reject_draft(
    session_id: str,
    draft_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_service = ChatService(db)
    res = await chat_service.reject_draft(session_id, draft_id, current_user)
    return SuccessMessageResponse(message=res["message"])

