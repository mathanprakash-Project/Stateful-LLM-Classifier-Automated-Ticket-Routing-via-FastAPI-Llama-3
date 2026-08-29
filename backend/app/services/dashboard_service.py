"""
Dashboard service for real-time ticket analytics and summary statistics.
"""

from typing import List
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Ticket, TicketCategory, User
from app.schemas.dashboard import CategoryMetric, DashboardStats, PriorityMetric
from app.schemas.ticket import TicketListSummary


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self, user: User) -> DashboardStats:
        user_roles = [r.name.lower() for r in user.roles]
        filter_user = "admin" not in user_roles and "manager" not in user_roles and "agent" not in user_roles

        base_stmt = select(Ticket)
        if filter_user:
            base_stmt = base_stmt.where(Ticket.created_by_id == user.id)

        # 1. Total counts by status
        status_stmt = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
        if filter_user:
            status_stmt = status_stmt.where(Ticket.created_by_id == user.id)
        
        status_res = await self.db.execute(status_stmt)
        status_counts = dict(status_res.all())

        total = sum(status_counts.values())
        open_c = status_counts.get("open", 0)
        assigned_c = status_counts.get("assigned", 0)
        in_prog_c = status_counts.get("in_progress", 0)
        resolved_c = status_counts.get("resolved", 0)
        closed_c = status_counts.get("closed", 0)
        escalated_c = status_counts.get("escalated", 0)

        # 2. Priority breakdown
        prio_stmt = select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
        if filter_user:
            prio_stmt = prio_stmt.where(Ticket.created_by_id == user.id)
        prio_res = await self.db.execute(prio_stmt)
        priority_distribution = [PriorityMetric(priority=p, count=c) for p, c in prio_res.all()]

        # 3. Category breakdown
        cat_stmt = (
            select(TicketCategory.name, func.count(Ticket.id))
            .join(Ticket, Ticket.category_id == TicketCategory.id)
            .group_by(TicketCategory.name)
        )
        if filter_user:
            cat_stmt = cat_stmt.where(Ticket.created_by_id == user.id)
        cat_res = await self.db.execute(cat_stmt)
        category_distribution = [CategoryMetric(category_name=name, count=c) for name, c in cat_res.all()]

        # 4. Recent tickets (latest 10)
        recent_stmt = (
            select(Ticket)
            .options(
                selectinload(Ticket.creator),
                selectinload(Ticket.assignee),
                selectinload(Ticket.category),
            )
            .order_by(desc(Ticket.created_at))
            .limit(10)
        )
        if filter_user:
            recent_stmt = recent_stmt.where(Ticket.created_by_id == user.id)
        recent_res = await self.db.execute(recent_stmt)
        recent_models = recent_res.scalars().all()

        recent_summaries = [
            TicketListSummary(
                id=t.id,
                ticket_number=t.ticket_number,
                title=t.title,
                priority=t.priority,
                status=t.status,
                category_name=t.category.name if t.category else None,
                creator_name=t.creator.full_name if t.creator else None,
                assignee_name=t.assignee.full_name if t.assignee else None,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in recent_models
        ]

        return DashboardStats(
            total_tickets=total,
            open_tickets=open_c,
            assigned_tickets=assigned_c,
            in_progress_tickets=in_prog_c,
            resolved_tickets=resolved_c,
            closed_tickets=closed_c,
            escalated_tickets=escalated_c,
            priority_distribution=priority_distribution,
            category_distribution=category_distribution,
            recent_tickets=recent_summaries,
        )

