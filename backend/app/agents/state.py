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
    messages: List[Dict[str, Any]]
    current_user_message: str

    # Intent
    intent: Optional[str]  # grievance_report | ticket_status | general_query | draft_modification

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

