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
    
    # Operational Maintenance Activity checks
    act_code = state.get("activity_code", state.get("intent", "UNKNOWN"))
    from app.core.activity_registry import get_activity
    act_def = get_activity(act_code)

    # Core requirements
    title = extracted.get("title")
    desc = extracted.get("description")
    cat = extracted.get("category")
    
    is_maintenance_act = act_def and act_def.activity_code not in ["UNKNOWN", "SERVER", "DATABASE", "NETWORK", "SECURITY"]

    if not is_maintenance_act:
        if not title or len(str(title).strip()) < 4:
            missing_fields.append("title")
        if not desc or len(str(desc).strip()) < 8:
            missing_fields.append("description")
        if not cat:
            missing_fields.append("category")

    all_user_text = " ".join([m.get("content", "") for m in messages if m.get("role") == "user"])
    if state.get("current_user_message"):
        all_user_text += " " + state.get("current_user_message")
    all_user_text_lower = all_user_text.lower()

    if act_def and act_def.prerequisites:
        # Check if user has answered the prerequisite status
        has_prereq_ack = any(w in all_user_text_lower for w in ["yes", "done", "completed", "verified", "ready", "ok", "prepared", "prereq"])
        if not has_prereq_ack:
            missing_fields.append("prerequisites_status")

        # Check if user has specified downtime / maintenance window
        if act_def.downtime_required or act_def.execution_mode == "Hybrid":
            has_downtime_window = any(w in all_user_text_lower for w in ["am", "pm", "utc", "gmt", "est", "pst", "ist", "saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "weekend", "night", "midnight", "tomorrow", "window", "hour", "hours", "downtime", "schedule", "at ", "from ", "between "])
            if not has_downtime_window or len(all_user_text.split()) < 6:
                missing_fields.append("maintenance_window")

    # Multi-turn diagnostic check for general tickets:
    # If the user only sent a single brief message, prompt for diagnostic clarification.
    affected = extracted.get("affected_system")
    troubleshooting = extracted.get("troubleshooting_tried")
    impact = extracted.get("impact_level")
    
    is_very_detailed_first_message = (
        user_turn_count == 1 and
        desc and len(desc.split()) >= 20 and
        (affected or troubleshooting or impact)
    )
    
    if user_turn_count < 2 and not is_very_detailed_first_message and not (act_def and act_def.prerequisites):
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
