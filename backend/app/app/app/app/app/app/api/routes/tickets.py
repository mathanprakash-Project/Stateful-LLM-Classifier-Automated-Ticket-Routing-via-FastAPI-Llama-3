"""
Ticket management routes: CRUD, status transition, comments, and history.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.schemas.common import PaginatedResponse
from app.schemas.ticket import (
    TicketCommentCreate,
    TicketCommentResponse,
    TicketCreate,
    TicketListSummary,
    TicketResponse,
    TicketUpdate,
)
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_in: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.create_ticket(current_user, ticket_in)


@router.get("", response_model=PaginatedResponse[TicketListSummary])
async def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    items, total = await ticket_service.list_tickets(
        user=current_user,
        status=status,
        priority=priority,
        category_id=category_id,
        search=search,
        page=page,
        per_page=per_page,
    )
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    summaries = [
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
        for t in items
    ]
    return PaginatedResponse(
        items=summaries,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.get_ticket(ticket_id, current_user)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    updates: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.update_ticket(ticket_id, current_user, updates)


@router.post("/{ticket_id}/comments", response_model=TicketCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    ticket_id: str,
    comment_in: TicketCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.add_comment(
        ticket_id=ticket_id,
        user=current_user,
        content=comment_in.content,
        is_internal=comment_in.is_internal,
    )


@router.post("/{ticket_id}/approve", response_model=TicketResponse)
async def approve_operation(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.approve_restricted_operation(ticket_id, current_user, db)


@router.post("/{ticket_id}/reject", response_model=TicketResponse)
async def reject_operation(
    ticket_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    reason = body.get("reason", "No reason provided")
    return await ticket_service.reject_restricted_operation(ticket_id, current_user, reason, db)


@router.post("/{ticket_id}/execute", response_model=TicketResponse)
async def execute_operation(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.execute_restricted_operation(ticket_id, current_user, db)


@router.post("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket_endpoint(
    ticket_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent_id = body.get("agent_id")
    if not agent_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="agent_id is required")
    ticket_service = TicketService(db)
    return await ticket_service.assign_to_agent(ticket_id, current_user, agent_id, db)


@router.post("/{ticket_id}/start-work", response_model=TicketResponse)
async def start_work_endpoint(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.start_work(ticket_id, current_user, db)


@router.post("/{ticket_id}/complete-work", response_model=TicketResponse)
async def complete_work_endpoint(
    ticket_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notes = body.get("notes", "Activity completed successfully.")
    ticket_service = TicketService(db)
    return await ticket_service.complete_work(ticket_id, current_user, notes, db)


@router.post("/{ticket_id}/route", response_model=TicketResponse)
async def route_ticket_endpoint(
    ticket_id: str,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    target_team = body.get("target_team")
    if not target_team:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="target_team is required")
    return await ticket_service.route_ticket(ticket_id, current_user, target_team, db)


@router.delete("/{ticket_id}", status_code=status.HTTP_200_OK)
async def delete_ticket_endpoint(
    ticket_id: str,
    current_user: User = Depends(require_role("manager")),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.delete_ticket(ticket_id, current_user)


@router.post("/{ticket_id}/archive", response_model=TicketResponse)
async def archive_ticket_endpoint(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.archive_ticket(ticket_id, current_user, db)


@router.post("/{ticket_id}/renew", response_model=TicketResponse)
async def renew_ticket_endpoint(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.renew_ticket(ticket_id, current_user, db)


@router.post("/{ticket_id}/reopen", response_model=TicketResponse)
async def reopen_ticket_endpoint(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ticket_service = TicketService(db)
    return await ticket_service.reopen_ticket(ticket_id, current_user, db)


