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
        
        is_user = "user" in user_roles and not any(r in user_roles for r in ["agent", "manager", "admin"])
        is_agent = "agent" in user_roles
        is_manager = "manager" in user_roles
        is_admin = "admin" in user_roles

        base_stmt = select(Ticket)
        
        # Determine filter
        def apply_role_filter(stmt):
            if is_admin:
                return stmt
            if is_manager:
                return stmt
            if is_agent:
                from sqlalchemy import or_
                return stmt.where(or_(Ticket.assigned_to_id == user.id, Ticket.assigned_to_id == None))
            # if only user
            return stmt.where(Ticket.created_by_id == user.id)

        # 1. Total counts by status
        status_stmt = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
        status_stmt = apply_role_filter(status_stmt)
        
        status_res = await self.db.execute(status_stmt)
        status_counts = dict(status_res.all())

        total = sum(status_counts.values())
        open_c = status_counts.get("open", 0)
        assigned_c = status_counts.get("assigned", 0)
        in_prog_c = status_counts.get("in_progress", 0)
        resolved_c = status_counts.get("resolved", 0)
        closed_c = status_counts.get("closed", 0)
        escalated_c = status_counts.get("escalated", 0)
        pending_routing_c = status_counts.get("pending_manager_routing", 0)
        pending_approval_c = status_counts.get("pending_admin_approval", 0)

        # 2. Priority breakdown
        prio_stmt = select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
        prio_stmt = apply_role_filter(prio_stmt)
        prio_res = await self.db.execute(prio_stmt)
        priority_distribution = [PriorityMetric(priority=p, count=c) for p, c in prio_res.all()]

        # 3. Category breakdown
        cat_stmt = (
            select(TicketCategory.name, func.count(Ticket.id))
            .join(Ticket, Ticket.category_id == TicketCategory.id)
            .group_by(TicketCategory.name)
        )
        cat_stmt = apply_role_filter(cat_stmt)
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
        recent_stmt = apply_role_filter(recent_stmt)
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
                activity_code=t.activity_code,
                operation_status=t.operation_status,
                requires_admin_approval=t.requires_admin_approval,
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
            pending_routing_tickets=pending_routing_c,
            pending_approval_tickets=pending_approval_c,
            priority_distribution=priority_distribution,
            category_distribution=category_distribution,
            recent_tickets=recent_summaries,
        )

