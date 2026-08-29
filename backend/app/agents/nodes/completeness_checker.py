"""
Completeness checker node for validating ticket fields and enforcing multi-turn diagnostic triage.
"""

from typing import Any, Dict
from app.agents.state import AgentState


def check_completeness_node(state: AgentState) -> Dict[str, Any]:
    """
    Evaluates extracted information.
    Ensures the agent asks intelligent clarifying/diagnostic questions first
    before jumping straight to drafting a ticket on a single brief prompt.
    """
    extracted = state.get("extracted_fields") or {}
    messages = state.get("messages") or []
    
    # Count user messages in the session
    user_turn_count = sum(1 for m in messages if m.get("role") == "user")
    if state.get("current_user_message"):
        user_turn_count += 1
    
    missing_fields = []
    
    # Core requirements
    title = extracted.get("title")
    desc = extracted.get("description")
    cat = extracted.get("category")
    
    if not title or len(str(title).strip()) < 4:
        missing_fields.append("title")
    if not desc or len(str(desc).strip()) < 8:
        missing_fields.append("description")
    if not cat:
        missing_fields.append("category")
        
    # Multi-turn diagnostic check:
    # If the user only sent a single message and hasn't specified affected system/troubleshooting,
    # prompt for diagnostic clarification rather than instantly creating a draft.
    affected = extracted.get("affected_system")
    troubleshooting = extracted.get("troubleshooting_tried")
    impact = extracted.get("impact_level")
    
    is_very_detailed_first_message = (
        user_turn_count == 1 and
        desc and len(desc.split()) >= 20 and
        (affected or troubleshooting or impact)
    )
    
    if user_turn_count < 2 and not is_very_detailed_first_message:
        if not affected:
            missing_fields.append("affected_system")
        if not troubleshooting:
            missing_fields.append("troubleshooting_steps")
            
    is_complete = len(missing_fields) == 0

    return {
        "is_complete": is_complete,
        "missing_fields": missing_fields,
    }


completeness_checker_node = check_completeness_node
