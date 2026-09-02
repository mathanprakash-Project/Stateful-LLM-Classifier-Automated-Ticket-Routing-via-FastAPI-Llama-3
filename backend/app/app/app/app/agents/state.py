"""
Agent state definitions for LangGraph orchestration.
"""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
import operator


class AgentState(TypedDict):
    # Context
    session_id: str
    user_id: str
    user_name: Optional[str]
    user_role: Optional[str]  # "user", "agent" (employee), "manager", "admin"
    preferred_model: Optional[str]
    messages: List[Dict[str, Any]]
    current_user_message: str

    # Intent
    intent: Optional[str]  # Maps to ActivityCode values like APPLICATION_UI, SERVER, etc., or intent like ticket_status, general_query
    
    # Activity Classification
    activity_code: str          # From ActivityCode enum values
    technical_scope: str        # "application" | "out_of_application_scope" | "non_technical"
    confidence: float           # 0.0 - 1.0
    required_team: str          # "APPLICATION_SUPPORT", "DATABASE", etc.
    restricted_operation: bool
    requires_admin_approval: bool
    requires_manager_review: bool
    ticket_eligible: bool

    # Extracted fields
    extracted_fields: Dict[str, Any]
    missing_fields: List[str]

    # Draft
    draft: Optional[Dict[str, Any]]
    draft_id: Optional[str]
    draft_status: Optional[str]  # pending_review | approved | rejected

    # Control
    needs_human_approval: bool
    ticket_created: Optional[Dict[str, Any]]
    response_text: Optional[str]
    error: Optional[str]

