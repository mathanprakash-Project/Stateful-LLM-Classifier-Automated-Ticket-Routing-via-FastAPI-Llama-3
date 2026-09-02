"""
Ticket service handling business logic, validation, state machine transitions, and notifications.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationError,
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
        # Check permissions: only requester user profile can create tickets
        user_roles = [r.name.lower() for r in user.roles] if user.roles else ["user"]
        if "user" not in user_roles:
            raise AuthorizationError("Only requester user profile is authorized to create tickets.")

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
        
        # Resolve activity metadata if provided
        act_code = data.activity_code or "UNKNOWN"
        from app.core.activity_registry import get_activity
        act_def = get_activity(act_code)

        requires_admin_approval = data.requires_admin_approval or act_def.requires_admin_approval
        technical_scope = data.technical_scope or act_def.technical_scope
        responsible_team = data.responsible_team or act_def.responsible_team
        execution_mode = data.execution_mode or act_def.execution_mode
        downtime_required = data.downtime_required or act_def.downtime_required
        
        if requires_admin_approval:
            status = "pending_admin_approval"
            op_status = "pending"
        elif act_def.requires_manager_review or (responsible_team and responsible_team not in ["APPLICATION_SUPPORT", "NONE"]):
            status = "pending_manager_routing"
            op_status = "not_applicable"
        else:
            status = "open"
            op_status = "not_applicable"

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
            activity_code=act_code,
            technical_scope=technical_scope,
            operation_status=data.operation_status or op_status,
            responsible_team=responsible_team,
            requires_admin_approval=requires_admin_approval,
            status=status,
            execution_mode=execution_mode,
            downtime_required=downtime_required,
            downtime_acknowledged=data.downtime_acknowledged,
            prerequisites_confirmed=data.prerequisites_confirmed,
            prerequisites_notes=data.prerequisites_notes,
        )

        # Audit log
        await self.audit_repo.log_action(
            user_id=user.id,
            action="ticket:created",
            resource="ticket",
            resource_id=ticket.id,
            details={
                "ticket_number": ticket.ticket_number,
                "priority": ticket.priority,
                "activity_code": act_code,
                "downtime_acknowledged": data.downtime_acknowledged,
                "prerequisites_confirmed": data.prerequisites_confirmed,
            },
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
                meta = dict(ticket.meta_info or {})
                current_reopens = meta.get("reopen_count", 0)
                if current_reopens >= 3:
                    raise ValidationError(
                        "This ticket has already reached the maximum limit of 3 reopens and cannot be reopened further."
                    )
                meta["reopen_count"] = current_reopens + 1
                ticket.meta_info = meta
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

    async def _get_ticket_for_update(self, ticket_id: str, user: User, session=None) -> Ticket:
        # Internal helper
        ticket = await self.get_ticket(ticket_id, user)
        return ticket

    async def approve_restricted_operation(self, ticket_id: str, admin_user: User, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, admin_user, session)
        if ticket.operation_status != "pending":
            raise ValidationError("Operation is not in pending state")
        user_roles = [r.name.lower() for r in admin_user.roles]
        if "admin" not in user_roles:
            raise ValidationError("Only admin can approve restricted operations")
        
        validate_transition(ticket.status, "approved", user_roles)
        
        old_status = ticket.status
        ticket.status = "approved"
        ticket.operation_status = "approved"
        ticket.version += 1
        
        await self.ticket_repo.record_history(ticket.id, admin_user.id, "status", old_status, "approved", "Admin approved restricted operation")
        await self.ticket_repo.record_history(ticket.id, admin_user.id, "operation_status", "pending", "approved", "Restricted operation approved")
        await self.audit_repo.log_action(
            user_id=admin_user.id,
            action="admin:approved_operation",
            resource="ticket",
            resource_id=ticket.id,
            details={"ticket_number": ticket.ticket_number},
        )
        
        await session.commit()
        await notification_service.broadcast("ticket_updated", {"ticket_id": ticket.id})
        return ticket

    async def reject_restricted_operation(self, ticket_id: str, admin_user: User, reason: str, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, admin_user, session)
        if ticket.operation_status != "pending":
            raise ValidationError("Operation is not in pending state")
        user_roles = [r.name.lower() for r in admin_user.roles]
        if "admin" not in user_roles:
            raise ValidationError("Only admin can reject restricted operations")
            
        validate_transition(ticket.status, "rejected", user_roles)
        
        old_status = ticket.status
        ticket.status = "rejected"
        ticket.operation_status = "rejected"
        ticket.version += 1
        
        await self.ticket_repo.add_comment(ticket.id, admin_user.id, f"Operation rejected: {reason}", is_internal=False)
        await self.ticket_repo.record_history(ticket.id, admin_user.id, "status", old_status, "rejected", "Admin rejected restricted operation")
        await self.ticket_repo.record_history(ticket.id, admin_user.id, "operation_status", "pending", "rejected", f"Restricted operation rejected: {reason}")
        
        await session.commit()
        await notification_service.broadcast("ticket_updated", {"ticket_id": ticket.id})
        return ticket

    async def execute_restricted_operation(self, ticket_id: str, admin_user: User, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, admin_user, session)
        if ticket.operation_status != "approved":
            raise ValidationError("Operation must be approved before execution")
        user_roles = [r.name.lower() for r in admin_user.roles]
        if "admin" not in user_roles:
            raise ValidationError("Only admin can execute restricted operations")
            
        validate_transition(ticket.status, "resolved", user_roles)
        
        old_status = ticket.status
        ticket.status = "resolved"
        ticket.operation_status = "completed"
        ticket.resolved_at = datetime.now(timezone.utc)
        ticket.version += 1
        
        await self.ticket_repo.record_history(ticket.id, admin_user.id, "status", old_status, "resolved", "Admin executed restricted operation")
        await self.ticket_repo.record_history(ticket.id, admin_user.id, "operation_status", "approved", "completed", "Restricted operation completed")
        
        await session.commit()
        await notification_service.broadcast("ticket_updated", {"ticket_id": ticket.id})
        return ticket

    async def route_ticket(self, ticket_id: str, manager_user: User, target_team: str, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, manager_user, session)
        if ticket.status != "pending_manager_routing":
            raise ValidationError("Ticket is not pending manager routing")
        user_roles = [r.name.lower() for r in manager_user.roles]
        if "manager" not in user_roles and "admin" not in user_roles:
            raise ValidationError("Only manager or admin can route tickets")
            
        validate_transition(ticket.status, "routed", user_roles)
        
        old_status = ticket.status
        ticket.status = "routed"
        ticket.routed_to_team = target_team
        ticket.routed_by_id = manager_user.id
        ticket.routed_at = datetime.now(timezone.utc)
        ticket.version += 1

        await self.ticket_repo.record_history(ticket.id, manager_user.id, "status", old_status, "routed", f"Routed to {target_team}")
        await session.commit()
        await notification_service.broadcast("ticket_updated", {"ticket_id": ticket.id})
        return ticket

    async def assign_to_agent(self, ticket_id: str, assigner_user: User, agent_user_id: str, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, assigner_user, session)
        user_roles = [r.name.lower() for r in assigner_user.roles]
        if "admin" not in user_roles and "manager" not in user_roles and "agent" not in user_roles:
            raise ValidationError("Only admin, manager, or agent can assign tickets")

        target_status = "assigned"
        validate_transition(ticket.status, target_status, user_roles)

        old_status = ticket.status
        old_assignee = ticket.assigned_to_id
        ticket.status = target_status
        ticket.assigned_to_id = agent_user_id
        ticket.version += 1

        await self.ticket_repo.record_history(ticket.id, assigner_user.id, "assigned_to_id", old_assignee, agent_user_id, "Ticket assigned to agent/employee")
        if old_status != target_status:
            await self.ticket_repo.record_history(ticket.id, assigner_user.id, "status", old_status, target_status, "Status updated on assignment")

        await session.commit()
        await notification_service.broadcast("ticket_updated", {"ticket_id": ticket.id})
        return ticket

    async def start_work(self, ticket_id: str, agent_user: User, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, agent_user, session)
        user_roles = [r.name.lower() for r in agent_user.roles]
        if "agent" not in user_roles and "admin" not in user_roles and "manager" not in user_roles:
            raise ValidationError("Only agents/employees can start work on tickets")

        validate_transition(ticket.status, "in_progress", user_roles)

        old_status = ticket.status
        ticket.status = "in_progress"
        if not ticket.assigned_to_id:
            ticket.assigned_to_id = agent_user.id
        ticket.version += 1

        await self.ticket_repo.record_history(ticket.id, agent_user.id, "status", old_status, "in_progress", "Agent started work on ticket")
        await session.commit()
        await notification_service.broadcast("ticket_updated", {"ticket_id": ticket.id})
        return ticket

    async def complete_work(self, ticket_id: str, agent_user: User, resolution_notes: str, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, agent_user, session)
        user_roles = [r.name.lower() for r in agent_user.roles]
        if "agent" not in user_roles and "admin" not in user_roles and "manager" not in user_roles:
            raise ValidationError("Only agents/employees can complete and resolve tickets")

        validate_transition(ticket.status, "resolved", user_roles)

        old_status = ticket.status
        ticket.status = "resolved"
        if ticket.operation_status in ["approved", "pending"]:
            ticket.operation_status = "completed"
        ticket.resolved_at = datetime.now(timezone.utc)
        ticket.version += 1

        if resolution_notes:
            await self.ticket_repo.add_comment(ticket.id, agent_user.id, f"Work Completed: {resolution_notes}", is_internal=False)

        await self.ticket_repo.record_history(ticket.id, agent_user.id, "status", old_status, "resolved", "Agent completed work and resolved ticket")
        await session.commit()
        await notification_service.broadcast(
            "ticket_resolved",
            {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "status": "resolved",
            }
        )
        await notification_service.broadcast(
            "ticket_updated",
            {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "status": "resolved",
            }
        )
        return ticket

    async def delete_ticket(self, ticket_id: str, user: User) -> dict:
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundError("Ticket", ticket_id)

        user_roles = [r.name.lower() for r in user.roles]
        if "manager" not in user_roles and "admin" not in user_roles:
            raise AuthorizationError("Only managers can delete tickets.")

        # Business Rule: Tickets can only be deleted after they are resolved (or closed)
        if ticket.status not in ["resolved", "closed", "cancelled"]:
            raise ValidationError(
                f"Ticket {ticket.ticket_number} cannot be deleted because its status is '{ticket.status}'. "
                "Tickets can only be deleted after they are resolved."
            )

        ticket_number = ticket.ticket_number
        ticket_title = ticket.title

        # Audit entry before deletion
        await self.audit_repo.log_action(
            action="ticket:delete",
            resource="ticket",
            user_id=user.id,
            resource_id=ticket.id,
            details={"ticket_number": ticket_number, "title": ticket_title, "status": ticket.status},
        )

        await self.ticket_repo.delete(ticket)
        await notification_service.broadcast("ticket_deleted", {"ticket_id": ticket_id, "ticket_number": ticket_number})
        return {"message": f"Ticket {ticket_number} deleted successfully", "id": ticket_id}

    async def archive_ticket(self, ticket_id: str, user: User, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, user, session)
        user_roles = [r.name.lower() for r in user.roles]
        validate_transition(ticket.status, "archived", user_roles)

        old_status = ticket.status
        ticket.status = "archived"
        ticket.version += 1

        await self.ticket_repo.record_history(ticket.id, user.id, "status", old_status, "archived", "Ticket moved to 2-month archive retention")
        await session.commit()
        await notification_service.broadcast("ticket_updated", {"ticket_id": ticket.id, "status": "archived"})
        return ticket

    async def renew_ticket(self, ticket_id: str, user: User, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, user, session)
        user_roles = [r.name.lower() for r in user.roles]
        
        # Validate that requester user owns ticket or staff
        if "user" in user_roles and "admin" not in user_roles and "manager" not in user_roles and "agent" not in user_roles:
            if ticket.creator_id != user.id:
                raise AuthorizationError("You can only renew and reopen your own archived tickets.")

        validate_transition(ticket.status, "reopened", user_roles)

        old_status = ticket.status
        ticket.status = "reopened"
        ticket.version += 1

        await self.ticket_repo.record_history(ticket.id, user.id, "status", old_status, "reopened", "Archived ticket renewed and reopened into active queue")
        await session.commit()
        await notification_service.broadcast("ticket_updated", {"ticket_id": ticket.id, "status": "reopened"})
        return ticket

    async def reopen_ticket(self, ticket_id: str, user: User, session: AsyncSession) -> Ticket:
        ticket = await self._get_ticket_for_update(ticket_id, user, session)
        user_roles = [r.name.lower() for r in user.roles]
        
        validate_transition(ticket.status, "reopened", user_roles)
        
        meta = dict(ticket.meta_info or {})
        reopen_count = meta.get("reopen_count", 0)
        if reopen_count >= 3:
            raise ValidationError(
                "This ticket has already reached the maximum limit of 3 reopens and cannot be reopened further."
        
        old_status = ticket.status
        ticket.resolved_at = None
        ticket.closed_at = None
        meta["reopen_count"] = reopen_count + 1
        ticket.meta_info = meta
        ticket.version += 1
        
        await self.ticket_repo.record_history(
            ticket.id,
            user.id,
            "status",
            old_status,
            "reopened",
            f"Ticket reopened (Reopen attempt {meta['reopen_count']} of 3)"
        )
        await session.commit()
        await notification_service.broadcast(
            "ticket_updated",
            {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "status": "reopened",
                "reopen_count": meta["reopen_count"]
            }
        )
        return ticket


