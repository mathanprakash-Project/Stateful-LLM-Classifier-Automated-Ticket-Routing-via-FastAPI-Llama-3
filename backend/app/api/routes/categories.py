"""
Category and subcategory endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.repositories.category_repo import CategoryRepository
from app.schemas.category import CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    repo = CategoryRepository(db)
    return await repo.list_all(active_only=True)


@router.get("/activities")
async def list_activities():
    from app.core.activity_registry import get_all_activities
    activities = get_all_activities()
    return [
        {
            "activity_code": a.activity_code,
            "activity_name": a.activity_name,
            "description": a.description,
            "technical_scope": a.technical_scope,
            "allowed_for_user_request": a.allowed_for_user_request,
            "restricted_operation": a.restricted_operation,
            "required_role_for_execution": a.required_role_for_execution,
            "responsible_team": a.responsible_team,
            "requires_admin_approval": a.requires_admin_approval,
            "requires_manager_review": a.requires_manager_review,
            "ticket_eligible": a.ticket_eligible,
            "execution_mode": a.execution_mode,
            "downtime_required": a.downtime_required,
            "downtime_description": a.downtime_description,
            "customer_summary": a.customer_summary,
            "customer_analogy": a.customer_analogy,
            "prerequisites": a.prerequisites,
            "risk_warning": a.risk_warning,
            "approval_workflow": a.approval_workflow,
        }
        for a in activities
    ]

