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
    
    all_user_text = " ".join([m.get("content", "") for m in messages if m.get("role") == "user"])
    if state.get("current_user_message"):
        all_user_text += " " + state.get("current_user_message")
    all_user_lower = all_user_text.lower()

    # Operational Maintenance Activity checks
    act_code = state.get("activity_code") or state.get("intent") or "UNKNOWN"
    if act_code in ["UNKNOWN", "ActivityCode", None]:
        cat_name = str(extracted.get("category", "")).lower()
        if "version" in cat_name:
            act_code = "APPLICATION_VERSION"
        elif "client" in cat_name or "transfer" in cat_name:
            act_code = "CLIENT_DATA_TRANSFER"
        elif "file" in cat_name:
            act_code = "FILE_MANAGEMENT"
        elif "ui" in cat_name:
            act_code = "APPLICATION_UI"
        elif any(k in all_user_lower for k in ["application version", "version upgrade", "upgrade application", "downgrade application", "runtime engine", "version maintenance"]):
            act_code = "APPLICATION_VERSION"
        elif any(k in all_user_lower for k in ["client data transfer", "transfer data", "client 100", "client 200", "migrate client"]):
            act_code = "CLIENT_DATA_TRANSFER"
        elif any(k in all_user_lower for k in [
            "file management", "files management", "file mangement", "files mangements",
            "file permission", "file permissions", "permission for the files", "permissions for the files",
            "permission change", "file access", "archive logs", "housekeeping script"
        ]):
            act_code = "FILE_MANAGEMENT"

    from app.core.activity_registry import get_activity, check_prereq_ack, check_downtime_window, is_new_inquiry_start
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

    curr_msg = state.get("current_user_message", "")
    is_initial_start = is_new_inquiry_start(curr_msg)

    # Determine user messages that belong to the current active inquiry
    if is_initial_start:
        inquiry_user_msgs = [curr_msg]
    else:
        # Find the start of the current inquiry in messages
        inquiry_start_idx = 0
        for idx, msg in enumerate(messages):
            if msg.get("role") == "user":
                c = msg.get("content", "")
                if is_new_inquiry_start(c):
                    inquiry_start_idx = idx
            elif msg.get("role") == "assistant":
                if msg.get("message_type") in ["ticket_draft", "ticket_confirmation"]:
                    inquiry_start_idx = idx + 1

        inquiry_user_msgs = [
            m.get("content", "") for m in messages[inquiry_start_idx:]
            if m.get("role") == "user"
        ]
        if curr_msg:
            inquiry_user_msgs.append(curr_msg)

    if act_def and act_def.prerequisites:
        from app.core.activity_registry import is_prereq_explicitly_pending
        # If the user explicitly stated in their latest message that prerequisites are NOT done / pending
        if is_prereq_explicitly_pending(curr_msg):
            has_prereq_ack = False
        else:
            has_prereq_ack = any(check_prereq_ack(m) for m in inquiry_user_msgs)

        if not has_prereq_ack:
            missing_fields.append("prerequisites_status")

        # Check if user has specified downtime / maintenance window
        if act_def.downtime_required or act_def.execution_mode == "Hybrid":
            has_downtime_window = any(check_downtime_window(m) for m in inquiry_user_msgs)
            if not has_downtime_window:
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
