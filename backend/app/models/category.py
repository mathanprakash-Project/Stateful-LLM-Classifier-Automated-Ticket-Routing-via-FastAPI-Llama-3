"""
Ticket Category and Subcategory models.
"""

from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class TicketCategory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ticket_categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    subcategories: Mapped[List["TicketSubcategory"]] = relationship(
        "TicketSubcategory",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket",
        back_populates="category",
    )


class TicketSubcategory(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ticket_subcategories"

    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ticket_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    category: Mapped["TicketCategory"] = relationship(
        "TicketCategory",
        back_populates="subcategories",
    )
    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket",
        back_populates="subcategory",
    )

