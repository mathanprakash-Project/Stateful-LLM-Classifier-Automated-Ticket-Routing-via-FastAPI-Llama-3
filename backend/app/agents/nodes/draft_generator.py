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

    draft = {
        "title": title,
        "description": description,
        "category_name": category_name,
        "subcategory_name": subcategory_name,
        "priority": priority,
        "meta_info": {"affected_system": affected, "created_via": "ai_agent"},
    }

    return {
        "draft": draft,
        "needs_human_approval": True,
        "draft_status": "pending_review",
    }
