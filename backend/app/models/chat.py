"""
ChatSession, ChatMessage, and AITicketDraft models.
"""

from typing import Any, List, Optional
from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChatSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chat_sessions"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    agent_state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at.asc()",
        lazy="selectin",
    )
    drafts: Mapped[List["AITicketDraft"]] = relationship(
        "AITicketDraft",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ChatMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(30), default="text", nullable=False)
    metadata_info: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")


class AITicketDraft(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_ticket_drafts"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    ticket_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tickets.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending_review", nullable=False)  # pending_review, approved, rejected, expired
    draft_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="drafts")
    ticket: Mapped[Optional["Ticket"]] = relationship("Ticket", lazy="selectin")

