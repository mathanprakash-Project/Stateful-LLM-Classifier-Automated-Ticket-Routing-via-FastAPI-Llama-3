"""
Ticket, TicketComment, TicketAttachment, and TicketHistory models.
"""

from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Ticket(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tickets"

    ticket_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    assigned_to_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    category_id: Mapped[str] = mapped_column(String(36), ForeignKey("ticket_categories.id"), nullable=False, index=True)
    subcategory_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("ticket_subcategories.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(30), default="medium", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False, index=True)
    meta_info: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    activity_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    technical_scope: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    operation_status: Mapped[Optional[str]] = mapped_column(String(30), default="not_applicable", nullable=True)
    responsible_team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    requires_admin_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    routed_to_team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    routed_by_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    routed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Operational Maintenance & Governance
    execution_mode: Mapped[Optional[str]] = mapped_column(String(30), default="Online", nullable=True)
    downtime_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    downtime_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prerequisites_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prerequisites_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="tickets_created",
        lazy="selectin",
    )
    routed_by = relationship("User", foreign_keys=[routed_by_id])
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        back_populates="tickets_assigned",
        lazy="selectin",
    )
    category: Mapped["TicketCategory"] = relationship(
        "TicketCategory",
        back_populates="tickets",
        lazy="selectin",
    )
    subcategory: Mapped[Optional["TicketSubcategory"]] = relationship(
        "TicketSubcategory",
        back_populates="tickets",
        lazy="selectin",
    )
    comments: Mapped[List["TicketComment"]] = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketComment.created_at.asc()",
        lazy="selectin",
    )
    attachments: Mapped[List["TicketAttachment"]] = relationship(
        "TicketAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    history: Mapped[List["TicketHistory"]] = relationship(
        "TicketHistory",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketHistory.created_at.asc()",
        lazy="selectin",
    )


class TicketComment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ticket_comments"

    ticket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        nullable=False,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments", lazy="selectin")


class TicketAttachment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ticket_attachments"

    ticket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        nullable=False,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="attachments")


class TicketHistory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ticket_history"

    ticket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    changed_by_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        nullable=False,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="history")
    changed_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

