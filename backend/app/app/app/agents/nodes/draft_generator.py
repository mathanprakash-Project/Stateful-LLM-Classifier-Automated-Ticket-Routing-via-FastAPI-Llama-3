"""
Draft generator node for LangGraph agent with strict technical validation.
Generates structured ticket draft card for human review.
"""

from typing import Any, Dict
from app.agents.nodes.info_extractor import is_text_out_of_scope
from app.agents.state import AgentState


async def generate_draft_node(state: AgentState) -> Dict[str, Any]:
    extracted = state.get("extracted_fields", {})

    category_name = extracted.get("category", "Software")
    subcategory_name = extracted.get("subcategory", "General Inquiry")
    priority = extracted.get("priority", "medium")
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
        elif any(k in search_space for k in ["transfer", "client", "data migration", "sync"]):
            act_code = "CLIENT_DATA_TRANSFER"
            act_code = "FILE_MANAGEMENT"
        else:

    # Map static activity titles and mode-based default priorities
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
        act_code = "APPLICATION_UI"
        category_name = "Application UI"
        subcategory_name = "UI Bug"
    # Use extracted priority if explicitly specified by user, else default by execution mode
    final_priority = extracted.get("priority") or mode_priority

    messages = state.get("messages", [])
    user_msgs = [m.get("content", "") for m in messages if m.get("role") == "user"]
    if state.get("current_user_message"):
        "description": description,
        "category_name": category_name,
        "meta_info": {"affected_system": affected, "created_via": "ai_agent"},
        "requires_admin_approval": act_def.requires_admin_approval,
        "requires_manager_review": act_def.requires_manager_review,
        "responsible_team": act_def.responsible_team,
        "execution_mode": act_def.execution_mode,
        "downtime_required": act_def.downtime_required,
        "downtime_description": act_def.downtime_description,
        "prerequisites": act_def.prerequisites,
        "risk_warning": act_def.risk_warning,
        "maintenance_window": last_user_text,
        "prerequisites_notes": f"Maintenance Window / Schedule: {last_user_text}",
    }

    return {
        "draft": draft,
        "needs_human_approval": True,
    }
