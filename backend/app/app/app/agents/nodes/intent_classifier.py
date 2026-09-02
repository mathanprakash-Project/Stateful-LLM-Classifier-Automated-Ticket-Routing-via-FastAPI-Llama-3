"""
Intent classifier node for LangGraph agent with strict IT domain guardrails.
"""

import json
import logging
import re
from typing import Any, Dict

from app.agents.prompts.system_prompts import INTENT_CLASSIFIER_PROMPT
from app.agents.state import AgentState
from app.config.settings import settings
from app.core.activity_registry import get_activity
from app.core.llm_client import call_ollama

logger = logging.getLogger(__name__)

# Non-IT keywords that indicate out-of-scope requests
OUT_OF_SCOPE_KEYWORDS = [
    "pant", "pants", "cargo", "jeans", "shirt", "tshirt", "t-shirt", "dress", "clothes", "clothing",
    "shoe", "shoes", "wear", "zudio", "zara", "h&m", "fabric", "tailor", "tight", "loose",
    "food", "pizza", "burger", "coffee", "lunch", "dinner", "recipe", "cook", "hungry",
    "movie", "song", "lyrics", "cricket", "football", "match", "joke", "funny", "dating", "love",
    "medical", "doctor", "headache", "fever", "medicine", "pill", "hospital",
    "leave", "salary", "hr", "hotel", "resume", "office location"
]

# Explicit IT / Technical keywords
IT_KEYWORDS = [
    "button", "page", "screen", "login", "form", "field", "dropdown", "ui", "layout", "validation", "submit",
    "application", "app", "version", "upgrade", "downgrade", "patch", "client", "transfer", "migrate", "data",
    "file", "upload", "download", "configuration", "error message", "not working", "broken", "missing",
    "server", "database", "db", "cpu", "memory", "disk", "restart", "infrastructure", "windows server", "linux",
    "network", "firewall", "dns", "connectivity", "transfer data", "client 100", "client 200",
    "migrate client", "copy client", "client-to-client", "update application", "migrate version",
    "file upload", "file download", "file replace", "file config",
    # Hardware brands & terms
    "laptop", "monitor", "dell", "lenovo", "macbook", "thinkpad", "hp", "hdmi", "usb", "keyboard", "mouse",
    "printer", "scanner", "docking", "charger", "battery", "display", "projector",
    # OS & software
    "windows", "macos", "chrome", "outlook", "excel", "word", "teams", "office", "browser", "software",
    # Troubleshooting & impact terms
    "reboot", "rebooting", "restart", "reinstall", "uninstall", "update", "crash", "freeze", "hang",
    "slow", "blocks", "blocking", "intermittent", "error", "bug", "glitch", "fails", "failed", "down",
    # Network terms
    "wifi", "wi-fi", "vpn", "airfiber", "airtel", "router", "ethernet", "bandwidth", "ping",
    # Access terms
    "password", "mfa", "2fa", "locked", "permission", "access", "authentication",
]


def rule_based_intent_fallback(text: str, conversation_history: list = None) -> Dict[str, Any]:
    lower = text.lower().strip()
    full_text = text
    if conversation_history:
        full_text = " ".join([m.get("content", "") for m in conversation_history if m.get("role") == "user"]) + " " + text
    full_lower = full_text.lower().strip()
    
    # 1. Check ticket status queries
    if any(k in lower for k in ["tkt-", "status of", "ticket status", "check ticket", "track ticket"]):
        return {"intent": "ticket_status", "activity_code": "UNKNOWN"}
    
    # 2. Check draft modifications
    if any(k in lower for k in ["change priority", "update draft", "edit title", "modify draft", "change category"]):
        return {"intent": "draft_modification", "activity_code": "UNKNOWN"}
    
    # 3. Check explicit capability / activity list / scope inquiries and greetings on standalone first turn
    scope_inquiry_keywords = [
        "activity list", "what activities", "explain the activities", "explain activities",
        "which activities", "list of activities", "what can you do", "what do you support",
        "under ur scope", "under your scope", "what tickets", "services", "capabilities", "hello", "hi",
        "hey", "good morning", "good afternoon", "who are you", "how can you help"
    ]
    is_standalone_greeting = (
        any(k == lower or lower.startswith(k) for k in scope_inquiry_keywords) and
        not any(w in full_lower for w in ["upgrade", "downgrade", "version", "patch", "transfer data", "client", "file", "ui", "broken", "issue"])
    )
    if is_standalone_greeting:
        return {"intent": "general_query", "activity_code": "UNKNOWN"}

    # 4. Version keywords (performing version actions)
    if any(k in full_lower for k in ["upgrade", "downgrade", "version", "patch", "update application", "migrate version", "application versioning"]):
        return {"intent": "APPLICATION_VERSION", "activity_code": "APPLICATION_VERSION"}

    # 5. Client data transfer (performing data transfer)
    if any(k in full_lower for k in ["transfer data", "client 100", "client 200", "migrate client", "copy client", "client-to-client", "data transfer"]):
        return {"intent": "CLIENT_DATA_TRANSFER", "activity_code": "CLIENT_DATA_TRANSFER"}

    # 6. File management
    if any(k in full_lower for k in ["file management", "upload file", "download file", "interface logs"]):
        return {"intent": "FILE_MANAGEMENT", "activity_code": "FILE_MANAGEMENT"}

    # 7. UI change
    if any(k in full_lower for k in ["ui change", "button broken", "layout issue", "form field"]):
        return {"intent": "APPLICATION_UI", "activity_code": "APPLICATION_UI"}

    # 8. Out-of-scope non-IT topics check
    has_out_of_scope = any(re.search(rf"\b{re.escape(kw)}\b", full_lower) for kw in OUT_OF_SCOPE_KEYWORDS)
    has_it_keyword = any(re.search(rf"\b{re.escape(kw)}\b", full_lower) for kw in IT_KEYWORDS)
    
    if has_out_of_scope and not has_it_keyword:
        return {"intent": "NON_TECHNICAL", "activity_code": "NON_TECHNICAL"}

    # 9. Default Application support (real issues)
    if has_it_keyword or any(w in full_lower for w in ["slow", "broken", "issue", "not working", "fails", "down", "glitch", "problem", "downtime", "prerequisite"]):
        return {"intent": "APPLICATION_OTHER", "activity_code": "APPLICATION_OTHER"}

    # If ambiguous and short
    if len(text.split()) < 4:
        return {"intent": "general_query", "activity_code": "UNKNOWN"}

    return {"intent": "APPLICATION_OTHER", "activity_code": "APPLICATION_OTHER"}


async def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    user_msg = state.get("current_user_message", "")
    messages = state.get("messages", [])
    existing_act = state.get("activity_code", "UNKNOWN")
    existing_intent = state.get("intent", "UNKNOWN")

    result = {}

    valid_codes = {
        "APPLICATION_UI", "APPLICATION_VERSION", "CLIENT_DATA_TRANSFER", "FILE_MANAGEMENT",
        "APPLICATION_OTHER", "SERVER", "DATABASE", "NETWORK", "SECURITY", "OTHER_TECHNICAL",
        "ticket_status", "draft_modification", "general_query", "NON_TECHNICAL"
    }

    if settings.LLM_PROVIDER != "mock":
        clean_msgs = messages[-4:]
        history_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in clean_msgs])
        prompt = f"{INTENT_CLASSIFIER_PROMPT}\n\nRecent Conversation:\n{history_text}\n\nLatest User Message: {user_msg}\n\nJSON Output:"
        response = await call_ollama(prompt, format_json=True)
        if response:
            try:
                parsed = json.loads(response)
                intent = parsed.get("intent", "").strip().upper()
                # Find matching valid code
                matched_code = next((c for c in valid_codes if c.upper() == intent), None)
                if matched_code and matched_code not in ["GENERAL_QUERY", "NON_TECHNICAL"]:
                    result["intent"] = matched_code
                    result["activity_code"] = matched_code if matched_code not in ["ticket_status", "draft_modification"] else "UNKNOWN"
                    result["confidence"] = parsed.get("confidence", 0.9)
            except Exception as exc:
                logger.warning("Failed to parse LLM intent classification response: %s", exc)

    if not result:
        res = rule_based_intent_fallback(user_msg, messages)
        result["intent"] = res["intent"]
        result["activity_code"] = res["activity_code"]
        result["confidence"] = 0.8

    # If an ongoing operational activity was already active in this session, keep it for follow-ups
    if existing_act not in ["UNKNOWN", "NON_TECHNICAL", None]:
        explicit_topic_change = bool(re.search(r"\b(what activities|explain activities|activity list|hello|hi|hey|tkt-|leave|salary|hr)\b", user_msg.lower()))
        if not explicit_topic_change:
            result["intent"] = existing_act
            result["activity_code"] = existing_act

    activity_code = result.get("activity_code", "UNKNOWN")
    activity_def = get_activity(activity_code)
    
    result["activity_code"] = activity_def.activity_code
    result["technical_scope"] = activity_def.technical_scope
    result["required_team"] = activity_def.responsible_team
    result["restricted_operation"] = activity_def.restricted_operation
    result["requires_admin_approval"] = activity_def.requires_admin_approval
    result["requires_manager_review"] = activity_def.requires_manager_review
    result["ticket_eligible"] = activity_def.ticket_eligible

    return result
