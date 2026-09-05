"""
Draft generator node for LangGraph agent with strict technical validation.
Generates structured ticket draft card for human review.
"""

from typing import Any, Dict
from app.agents.nodes.info_extractor import is_text_out_of_scope
from app.agents.state import AgentState
from app.core.activity_registry import get_activity


async def generate_draft_node(state: AgentState) -> Dict[str, Any]:
    extracted = state.get("extracted_fields", {})

    category_name = extracted.get("category", "Application UI")
    subcategory_name = extracted.get("subcategory", "General Inquiry")
    title = extracted.get("title", "Support Request")
    description = extracted.get("description", "No description provided.")
    affected = extracted.get("affected_system", "General")

    # Guard: Do not generate drafts for non-IT / out-of-scope topics
    if is_text_out_of_scope(title) and not any(w in description.lower() for w in ["laptop", "pc", "network", "wifi", "airfiber", "vpn", "internet", "software", "hardware"]):
        return {
            "draft": None,
            "needs_human_approval": False,
        }

    act_code = state.get("activity_code") or "UNKNOWN"
    if act_code in ["UNKNOWN", "ActivityCode", None]:
        search_space = f"{category_name} {subcategory_name} {title} {description} {state.get('intent', '')}".lower()
        if any(k in search_space for k in ["version", "upgrade", "downgrade", "patch", "binary"]):
            act_code = "APPLICATION_VERSION"
        elif any(k in search_space for k in ["transfer", "client", "data migration", "sync"]):
            act_code = "CLIENT_DATA_TRANSFER"
        elif any(k in search_space for k in ["file", "archive", "script", "upload", "download"]):
            act_code = "FILE_MANAGEMENT"
        else:
            act_code = "APPLICATION_UI"

    # Map static activity titles and mode-based default priorities
    if act_code == "APPLICATION_VERSION":
        category_name = "Application Version Maintenance"
        subcategory_name = "Version Upgrade"
        title = "Application Version Maintenance"
        mode_priority = "critical"  # Offline mode -> critical
    elif act_code == "CLIENT_DATA_TRANSFER":
        category_name = "Client Data Transfer"
        subcategory_name = "Data Migration"
        title = "Client Data Transfer"
        mode_priority = "high"  # Hybrid mode -> high
    elif act_code == "FILE_MANAGEMENT":
        category_name = "File Management"
        subcategory_name = "File Operations"
        title = "File Management Operations"
        mode_priority = "medium"  # Online mode -> medium
    else:
        act_code = "APPLICATION_UI"
        category_name = "Application UI"
        subcategory_name = "UI Bug"
        title = "Application UI Maintenance"
        mode_priority = "medium"  # Online mode -> medium
    messages = state.get("messages", [])
    all_user_text = " ".join([m.get("content", "") for m in messages if m.get("role") == "user"])
    if state.get("current_user_message"):
        all_user_text += " " + state.get("current_user_message")
    all_user_lower = all_user_text.lower()

    explicit_prio = None
    if any(k in all_user_lower for k in ["priority critical", "priority: critical", "priority is critical", "priority=critical"]):
        explicit_prio = "critical"
    elif any(k in all_user_lower for k in ["priority high", "priority: high", "priority is high", "priority=high"]):
        explicit_prio = "high"
    elif any(k in all_user_lower for k in ["priority low", "priority: low", "priority is low", "priority=low"]):
        explicit_prio = "low"
    elif any(k in all_user_lower for k in ["priority medium", "priority: medium", "priority is medium", "priority=medium"]):
        explicit_prio = "medium"

    # Default strictly to mode_priority (Online -> medium, Hybrid -> high, Offline -> critical)
    final_priority = explicit_prio or mode_priority

    act_def = get_activity(act_code)
    user_msgs = [m.get("content", "") for m in messages if m.get("role") == "user"]
    if state.get("current_user_message"):
        user_msgs.append(state.get("current_user_message"))

    from app.core.activity_registry import check_downtime_window
    window_val = None
    for umsg in reversed(user_msgs):
        if check_downtime_window(umsg):
            window_val = umsg.strip()
            break

    if not window_val:
        if act_def.downtime_required or act_def.execution_mode in ["Offline", "Hybrid"]:
            window_val = "Scheduled maintenance window verification pending."
        else:
            window_val = "No downtime required (Online Mode)."

    draft = {
        "title": title,
        "description": description,
        "category_name": category_name,
        "subcategory_name": subcategory_name,
        "priority": final_priority,
        "meta_info": {"affected_system": affected, "created_via": "ai_agent"},
        "activity_code": act_def.activity_code,
        "technical_scope": act_def.technical_scope,
        "restricted_operation": act_def.restricted_operation,
        "requires_admin_approval": act_def.requires_admin_approval,
        "requires_manager_review": act_def.requires_manager_review,
        "responsible_team": act_def.responsible_team,
        "execution_mode": act_def.execution_mode,
        "downtime_required": act_def.downtime_required,
        "downtime_description": act_def.downtime_description,
        "prerequisites": act_def.prerequisites,
        "risk_warning": act_def.risk_warning,
        "maintenance_window": window_val,
        "prerequisites_notes": f"Maintenance Window / Schedule: {window_val}",
    }

    return {
        "draft": draft,
        "needs_human_approval": True,
        "draft_status": "pending_review",
    }
