"""
Ticket repository for queries, filtering, creation, history and comments.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Ticket, TicketComment, TicketHistory, User


class TicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, ticket_id: str) -> Optional[Ticket]:
        stmt = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(
                selectinload(Ticket.creator),
                selectinload(Ticket.assignee),
                selectinload(Ticket.category),
                selectinload(Ticket.subcategory),
                selectinload(Ticket.comments).selectinload(TicketComment.author),
                selectinload(Ticket.history).selectinload(TicketHistory.changed_by),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ticket_number(self, ticket_number: str) -> Optional[Ticket]:
        stmt = (
            select(Ticket)
            .where(Ticket.ticket_number == ticket_number.strip().upper())
            .options(
                selectinload(Ticket.creator),
                selectinload(Ticket.assignee),
                selectinload(Ticket.category),
                selectinload(Ticket.subcategory),
                selectinload(Ticket.comments).selectinload(TicketComment.author),
                selectinload(Ticket.history).selectinload(TicketHistory.changed_by),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> Optional[Ticket]:
        if not key:
            return None
        stmt = select(Ticket).where(Ticket.idempotency_key == key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tickets(
        self,
        user_id: Optional[str] = None,
        assigned_to_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Ticket], int]:
        stmt = (
            select(Ticket)
            .options(
                selectinload(Ticket.creator),
                selectinload(Ticket.assignee),
                selectinload(Ticket.category),
                selectinload(Ticket.subcategory),
            )
            .order_by(desc(Ticket.created_at))
        )
        count_stmt = select(func.count(Ticket.id))

        if user_id:
            stmt = stmt.where(Ticket.created_by_id == user_id)
            count_stmt = count_stmt.where(Ticket.created_by_id == user_id)

        if assigned_to_id:
            stmt = stmt.where(Ticket.assigned_to_id == assigned_to_id)
            count_stmt = count_stmt.where(Ticket.assigned_to_id == assigned_to_id)

        if status:
            stmt = stmt.where(Ticket.status == status.lower())
            count_stmt = count_stmt.where(Ticket.status == status.lower())

        if priority:
            stmt = stmt.where(Ticket.priority == priority.lower())
            count_stmt = count_stmt.where(Ticket.priority == priority.lower())

        if category_id:
            stmt = stmt.where(Ticket.category_id == category_id)
            count_stmt = count_stmt.where(Ticket.category_id == category_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            filter_expr = or_(
                Ticket.title.ilike(search_pattern),
                Ticket.ticket_number.ilike(search_pattern),
                Ticket.description.ilike(search_pattern),
            )
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        res = await self.db.execute(stmt)
        tickets = list(res.scalars().all())

        return tickets, total

    async def create_ticket(
        self,
        ticket_number: str,
        created_by_id: str,
        category_id: str,
        title: str,
        description: str,
        priority: str = "medium",
        subcategory_id: Optional[str] = None,
        meta_info: Optional[dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Ticket:
        ticket = Ticket(
            ticket_number=ticket_number,
            created_by_id=created_by_id,
            category_id=category_id,
            subcategory_id=subcategory_id,
            title=title,
            description=description,
            priority=priority.lower(),
            status="open",
            meta_info=meta_info or {},
            idempotency_key=idempotency_key,
            version=1,
        )
        self.db.add(ticket)
        await self.db.flush()

        # Add initial history
        history = TicketHistory(
            ticket_id=ticket.id,
            changed_by_id=created_by_id,
            field_name="status",
            old_value=None,
            new_value="open",
            change_reason="Ticket created",
        )
        self.db.add(history)
        await self.db.commit()

        return await self.get_by_id(ticket.id)

    async def add_comment(
        self, ticket_id: str, user_id: str, content: str, is_internal: bool = False
    ) -> TicketComment:
        comment = TicketComment(
            ticket_id=ticket_id,
            user_id=user_id,
            content=content,
            is_internal=is_internal,
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def record_history(
        self,
        ticket_id: str,
        changed_by_id: Optional[str],
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str],
        change_reason: Optional[str] = None,
    ) -> TicketHistory:
        history = TicketHistory(
            ticket_id=ticket_id,
            changed_by_id=changed_by_id,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            change_reason=change_reason,
        )
        self.db.add(history)
        await self.db.flush()
        return history

