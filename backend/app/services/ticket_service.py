"""
Ticket service handling business logic, validation, state machine transitions, and notifications.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConcurrencyConflictError,
    DuplicateResourceError,
    NotFoundError,
    ValidationError,
)
from app.core.ticket_state_machine import validate_transition
from app.models import Ticket, TicketComment, User
from app.repositories.audit_repo import AuditRepository
from app.repositories.category_repo import CategoryRepository
from app.repositories.ticket_repo import TicketRepository
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.notification_service import notification_service
from app.utils.ticket_number import generate_ticket_number


class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.category_repo = CategoryRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_ticket(self, user: User, data: TicketCreate) -> Ticket:
        # Check idempotency key
        if data.idempotency_key:
            existing = await self.ticket_repo.get_by_idempotency_key(data.idempotency_key)
            if existing:
                return existing

        # Validate category
        category = await self.category_repo.get_by_id(data.category_id)
        if not category:
            raise ValidationError(f"Category '{data.category_id}' does not exist.")

        # Validate subcategory if provided
        if data.subcategory_id:
            sub = await self.category_repo.get_subcategory_by_id(data.subcategory_id)
            if not sub or sub.category_id != category.id:
                raise ValidationError(f"Invalid subcategory '{data.subcategory_id}' for category '{category.name}'.")

        ticket_number = generate_ticket_number()

        ticket = await self.ticket_repo.create_ticket(
            ticket_number=ticket_number,
            created_by_id=user.id,
            category_id=data.category_id,
            subcategory_id=data.subcategory_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            meta_info=data.meta_info,
            idempotency_key=data.idempotency_key,
        )

        # Audit log
        await self.audit_repo.log_action(
            user_id=user.id,
            action="ticket:created",
            resource="ticket",
            resource_id=ticket.id,
            details={"ticket_number": ticket.ticket_number, "priority": ticket.priority},
        )

        # Broadcast SSE notification
        await notification_service.broadcast(
            "ticket_created",
            {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "status": ticket.status,
                "priority": ticket.priority,
                "created_by": user.full_name,
            },
        )

        return ticket

    async def get_ticket(self, ticket_id: str, user: User) -> Ticket:
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundError("Ticket", ticket_id)

        user_roles = [r.name.lower() for r in user.roles]
        # Regular users can only read their own tickets
        if "admin" not in user_roles and "manager" not in user_roles and "agent" not in user_roles:
            if ticket.created_by_id != user.id:
                raise NotFoundError("Ticket", ticket_id)

        return ticket

    async def list_tickets(
        self,
        user: User,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Ticket], int]:
        user_roles = [r.name.lower() for r in user.roles]
        filter_user_id = None

        if "admin" not in user_roles and "manager" not in user_roles and "agent" not in user_roles:
            filter_user_id = user.id

        return await self.ticket_repo.list_tickets(
            user_id=filter_user_id,
            status=status,
            priority=priority,
            category_id=category_id,
            search=search,
            page=page,
            per_page=per_page,
        )

    async def update_ticket(self, ticket_id: str, user: User, data: TicketUpdate) -> Ticket:
        ticket = await self.get_ticket(ticket_id, user)
        user_roles = [r.name.lower() for r in user.roles]

        # Optimistic locking check
        if data.version is not None and ticket.version != data.version:
            raise ConcurrencyConflictError("Ticket version mismatch. Someone else may have updated this ticket.")

        now = datetime.now(timezone.utc)
        changes_recorded = False

        # Status transition
        if data.status and data.status.lower() != ticket.status.lower():
            target_status = data.status.lower()
            validate_transition(ticket.status, target_status, user_roles)

            old_status = ticket.status
            ticket.status = target_status

            if target_status == "resolved":
                ticket.resolved_at = now
            elif target_status == "closed":
                ticket.closed_at = now
            elif target_status == "reopened":
                ticket.resolved_at = None
                ticket.closed_at = None

            await self.ticket_repo.record_history(
                ticket_id=ticket.id,
                changed_by_id=user.id,
                field_name="status",
                old_value=old_status,
                new_value=target_status,
                change_reason=data.change_reason or data.comment or "Status transition",
            )
            changes_recorded = True

        # Assignee update
        if data.assigned_to_id is not None and data.assigned_to_id != ticket.assigned_to_id:
            old_assignee = ticket.assigned_to_id
            ticket.assigned_to_id = data.assigned_to_id
            await self.ticket_repo.record_history(
                ticket_id=ticket.id,
                changed_by_id=user.id,
                field_name="assigned_to",
                old_value=old_assignee,
                new_value=data.assigned_to_id,
                change_reason="Assignee changed",
            )
            changes_recorded = True

        # Priority update
        if data.priority and data.priority.lower() != ticket.priority.lower():
            old_priority = ticket.priority
            ticket.priority = data.priority.lower()
            await self.ticket_repo.record_history(
                ticket_id=ticket.id,
                changed_by_id=user.id,
                field_name="priority",
                old_value=old_priority,
                new_value=data.priority.lower(),
                change_reason="Priority changed",
            )
            changes_recorded = True

        # Title/Description updates
        if data.title and data.title != ticket.title:
            ticket.title = data.title
            changes_recorded = True
        if data.description and data.description != ticket.description:
            ticket.description = data.description
            changes_recorded = True

        # Add comment if attached
        if data.comment:
            await self.ticket_repo.add_comment(
                ticket_id=ticket.id,
                user_id=user.id,
                content=data.comment,
                is_internal=False,
            )

        if changes_recorded:
            ticket.version += 1
            ticket.updated_at = now
            await self.db.commit()

            # Broadcast update
            await notification_service.broadcast(
                "ticket_updated",
                {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "updated_by": user.full_name,
                },
            )

        return await self.ticket_repo.get_by_id(ticket.id)

    async def add_comment(self, ticket_id: str, user: User, content: str, is_internal: bool = False) -> TicketComment:
        ticket = await self.get_ticket(ticket_id, user)
        comment = await self.ticket_repo.add_comment(
            ticket_id=ticket.id,
            user_id=user.id,
            content=content,
            is_internal=is_internal,
        )
        await notification_service.broadcast(
            "ticket_updated",
            {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "event": "comment_added",
            },
        )
        return comment

