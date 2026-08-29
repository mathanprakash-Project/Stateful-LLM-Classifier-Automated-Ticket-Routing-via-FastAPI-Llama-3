"""
Chat session, message, and AI ticket draft repository.
"""

from typing import Any, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ChatSession, ChatMessage, AITicketDraft


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: str) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            status="active",
            agent_state={},
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(
                selectinload(ChatSession.messages),
                selectinload(ChatSession.drafts),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_sessions(self, user_id: str, limit: int = 20) -> List[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata_info: Optional[dict[str, Any]] = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata_info=metadata_info or {},
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def update_session_state(self, session_id: str, agent_state: dict[str, Any]):
        session = await self.get_session(session_id)
        if session:
            session.agent_state = agent_state
            await self.db.commit()

    async def create_draft(
        self,
        session_id: str,
        user_id: str,
        draft_data: dict[str, Any],
    ) -> AITicketDraft:
        draft = AITicketDraft(
            session_id=session_id,
            user_id=user_id,
            status="pending_review",
            draft_data=draft_data,
            revision=1,
        )
        self.db.add(draft)
        await self.db.commit()
        await self.db.refresh(draft)
        return draft

    async def get_draft(self, draft_id: str) -> Optional[AITicketDraft]:
        stmt = select(AITicketDraft).where(AITicketDraft.id == draft_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_draft(
        self, draft_id: str, draft_data: dict[str, Any], status: Optional[str] = None
    ) -> Optional[AITicketDraft]:
        draft = await self.get_draft(draft_id)
        if not draft:
            return None
        draft.draft_data = draft_data
        draft.revision += 1
        if status:
            draft.status = status
        await self.db.commit()
        await self.db.refresh(draft)
        return draft

