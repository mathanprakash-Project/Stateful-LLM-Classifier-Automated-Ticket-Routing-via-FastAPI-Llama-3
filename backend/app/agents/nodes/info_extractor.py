"""
Information extractor node for LangGraph agent.
Extracts ticket title, description, category, subcategory, priority, and metadata strictly for valid IT issues.
"""

import json
import logging
import re
from typing import Any, Dict

from app.agents.nodes.intent_classifier import OUT_OF_SCOPE_KEYWORDS
from app.agents.prompts.system_prompts import INFO_EXTRACTOR_PROMPT
from app.agents.state import AgentState
from app.config.settings import settings
from app.core.llm_client import call_ollama

logger = logging.getLogger(__name__)


def is_text_out_of_scope(text: str) -> bool:
    lower = text.lower()
    return any(re.search(rf"\b{re.escape(kw)}\b", lower) for kw in OUT_OF_SCOPE_KEYWORDS)


def rule_based_extraction_fallback(text: str, current_fields: Dict[str, Any], history: list = None) -> Dict[str, Any]:
    from app.core.activity_registry import is_new_inquiry_start
    lower = text.lower()
    full_text = text

    if is_new_inquiry_start(text):
        extracted = {}
        full_lower = lower
    else:
        extracted = dict(current_fields or {})
        if history:
            full_text = " ".join([m.get("content", "") for m in history if m.get("role") == "user"]) + " " + text
        full_lower = full_text.lower()

    # If the user input is out-of-scope noise, do NOT pollute technical fields
    if is_text_out_of_scope(text) and not any(w in lower for w in ["wifi", "airfiber", "vpn", "laptop", "pc", "network", "internet"]):
        return extracted

    # Category heuristic based on full conversation
    if any(w in full_lower for w in ["button", "layout", "page", "validation", "ui", "missing field"]):
        extracted["category"] = "Application UI"
        if "bug" in full_lower or "error" in full_lower:
            extracted["subcategory"] = "UI Bug"
        else:
            extracted["subcategory"] = "Enhancement Request"
    elif any(w in full_lower for w in ["upgrade", "downgrade", "version", "patch", "migrate version", "application versioning"]):
        extracted["category"] = "Application Version Maintenance"
        extracted["subcategory"] = "Version Upgrade"
    elif any(w in full_lower for w in ["transfer data", "client", "migrate client", "copy client", "client-to-client", "data transfer"]):
        extracted["category"] = "Client Data Transfer"
        extracted["subcategory"] = "Data Migration"
    elif any(w in full_lower for w in [
        "file", "files", "permission", "permissions", "access", "upload", "download", "replace",
        "interface logs", "housekeeping", "archive log", "archive logs"
    ]):
        extracted["category"] = "File Management"
        if any(w in full_lower for w in ["permission", "permissions", "access", "chmod"]):
            extracted["subcategory"] = "File Permissions / Access"
        elif any(w in full_lower for w in ["archive", "cleanup", "housekeeping"]):
            extracted["subcategory"] = "Log Archiving & Cleanup"
        else:
            extracted["subcategory"] = "File Operations"
    elif any(w in full_lower for w in ["server", "cpu", "memory", "deployment"]):
        extracted["category"] = "Server / Infrastructure"
        extracted["subcategory"] = "Server Down"
    elif any(w in full_lower for w in ["database", "db", "sql"]):
        extracted["category"] = "Database"
        extracted["subcategory"] = "DB Connection"
    elif any(w in full_lower for w in ["network", "vpn", "dns", "firewall"]):
        extracted["category"] = "Network"
        extracted["subcategory"] = "Connectivity Issue"
    elif any(w in full_lower for w in ["security", "access violation", "vulnerability"]):
        extracted["category"] = "Security"
        extracted["subcategory"] = "Access Violation"
    elif not extracted.get("category"):
        extracted["category"] = "Application Support"
        extracted["subcategory"] = "General Inquiry"

    # Priority heuristic (Only extract if explicitly stated by user, otherwise defer to activity execution mode default)
    if any(w in full_lower for w in ["priority critical", "priority: critical", "priority is critical", "priority=critical"]):
        extracted["priority"] = "critical"
    elif any(w in full_lower for w in ["priority high", "priority: high", "priority is high", "priority=high"]):
        extracted["priority"] = "high"
    elif any(w in full_lower for w in ["priority low", "priority: low", "priority is low", "priority=low"]):
        extracted["priority"] = "low"
    elif any(w in full_lower for w in ["priority medium", "priority: medium", "priority is medium", "priority=medium"]):
        extracted["priority"] = "medium"

    # Metadata heuristics
    if any(w in full_lower for w in ["dell", "macbook", "lenovo", "thinkpad", "windows", "macos", "linux", "airfiber", "airtel", "router"]):
        extracted["affected_system"] = text.strip()
    if any(w in full_lower for w in ["tried", "reboot", "restarting", "cable", "reset", "attempted", "reconnected", "hdmi"]):
        extracted["troubleshooting_tried"] = text.strip()

    # Title formulation
    if not extracted.get("title") or is_text_out_of_scope(extracted.get("title", "")):
        if "version" in full_lower or "upgrade" in full_lower:
            extracted["title"] = "Application Version Upgrade Maintenance"
        elif "transfer" in full_lower or "client" in full_lower:
            extracted["title"] = "Client Data Transfer Request"
        elif any(w in full_lower for w in ["permission", "permissions", "access"]) and any(w in full_lower for w in ["file", "files"]):
            extracted["title"] = "Update Application File Permissions"
        elif any(w in full_lower for w in ["file", "files", "archive", "log"]):
            extracted["title"] = "File Management Operations"
        elif "airfiber" in full_lower or "airtel" in full_lower:
            extracted["title"] = "Airtel AirFiber Unstable Connection"
        else:
            extracted["title"] = full_text[:60].strip().capitalize()
            if len(full_text) > 60:
                extracted["title"] += "..."
    
    # Description formulation
    if not extracted.get("description") or is_text_out_of_scope(extracted.get("description", "")):
        extracted["description"] = full_text.strip()
    else:
        if text.strip() not in extracted["description"] and not is_text_out_of_scope(text):
            extracted["description"] = f"{extracted['description']}\nSchedule / Notes: {text.strip()}"

    return extracted


async def extract_info_node(state: AgentState) -> Dict[str, Any]:
    from app.core.activity_registry import is_new_inquiry_start
    current_fields = state.get("extracted_fields", {})
    user_msg = state.get("current_user_message", "")

    if is_new_inquiry_start(user_msg):
        current_fields = {}
        clean_history = []
    else:
        # Filter out obvious non-IT messages from history sent to LLM
        clean_history = [
            m for m in state.get("messages", [])[-6:]
            if not is_text_out_of_scope(m.get("content", ""))
        ]

    history_text = "\n".join(
        f"{m.get('role', 'user')}: {m.get('content', '')}" for m in clean_history
    )
    history_text += f"\nuser: {user_msg}"

    if settings.LLM_PROVIDER != "mock":
        prompt_content = (
            f"{INFO_EXTRACTOR_PROMPT}\n\n"
            f"Conversation History:\n{history_text}\n\n"
            f"Existing Extracted Fields: {json.dumps(current_fields)}\n\n"
            f"JSON Output:"
        )
        response = await call_ollama(prompt_content, format_json=True)
        if response:
            try:
                parsed = json.loads(response)
                merged = dict(current_fields)
                for k, v in parsed.items():
                    if v and not (isinstance(v, str) and is_text_out_of_scope(v)):
                        merged[k] = v
                return {"extracted_fields": merged}
            except Exception as exc:
                logger.warning("LLM info extraction json parse fallback: %s", exc)

    extracted = rule_based_extraction_fallback(user_msg, current_fields, clean_history)
    return {"extracted_fields": extracted}
