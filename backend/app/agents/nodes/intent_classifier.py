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
from app.core.activity_registry import get_activity, is_greeting_or_activity_overview
from app.core.llm_client import call_ollama

logger = logging.getLogger(__name__)

# Non-IT keywords that indicate out-of-scope requests
OUT_OF_SCOPE_KEYWORDS = [
    # Clothing & Shopping
    "pant", "pants", "cargo", "jeans", "shirt", "tshirt", "t-shirt", "dress", "clothes", "clothing",
    "shoe", "shoes", "wear", "zudio", "zara", "h&m", "fabric", "tailor", "tight", "loose", "shop", "shopping", "mall", "market", "store",
    # Food & Dining
    "food", "pizza", "burger", "coffee", "tea", "lunch", "dinner", "recipe", "cook", "hungry",
    "ice cream", "icecream", "dessert", "sweet", "restaurant", "cafe", "snack", "eat", "drink", "biryani",
    # Entertainment & Sports
    "movie", "song", "lyrics", "cricket", "football", "match", "joke", "funny", "dating", "love",
    # Health & Medical
    "medical", "doctor", "headache", "fever", "medicine", "pill", "hospital",
    # Travel & Places & Weather
    "travel", "flight", "train", "bus", "hotel", "weather", "rain", "temperature", "forecast",
    "bangalore", "bengaluru", "delhi", "mumbai", "chennai", "hyderabad", "city", "place", "places", "tour", "tourism",
    # Non-IT corporate / HR
    "leave", "salary", "payroll", "hr", "appraisal", "hike", "resume", "interview", "office location", "cab"
]

# Explicit IT / Technical keywords
IT_KEYWORDS = [
    "activity", "activities", "maintenance", "operations",
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
    
    # 3. Check explicit capability / activity list / scope inquiries and greetings
    if is_greeting_or_activity_overview(text):
        return {"intent": "general_query", "activity_code": "UNKNOWN"}

    # 4. Version keywords (performing version actions)
    if any(k in full_lower for k in ["upgrade", "downgrade", "version", "patch", "update application", "migrate version", "application versioning"]):
        return {"intent": "APPLICATION_VERSION", "activity_code": "APPLICATION_VERSION"}

    # 5. Client data transfer (performing data transfer)
    if any(k in full_lower for k in ["transfer data", "client 100", "client 200", "migrate client", "copy client", "client-to-client", "data transfer"]):
        return {"intent": "CLIENT_DATA_TRANSFER", "activity_code": "CLIENT_DATA_TRANSFER"}

    # 6. File management
    file_management_keywords = [
        "file management", "files management", "file mangement", "files mangements",
        "file permission", "file permissions", "permission for the files", "permissions for the files",
        "permissions for files", "permission for files", "permission change", "permissions change",
        "change access and permissions", "file access", "directory permissions", "folder permissions",
        "archive log", "archive logs", "archiving logs", "log cleanup", "cleanup script", "cleanup scripts",
        "housekeeping script", "housekeeping scripts", "storage cleanup", "upload file", "download file",
        "file sync", "file processing"
    ]
    if any(k in full_lower for k in file_management_keywords):
        return {"intent": "FILE_MANAGEMENT", "activity_code": "FILE_MANAGEMENT"}

    # 7. UI change
    if any(k in full_lower for k in ["ui change", "button broken", "layout issue", "form field"]):
        return {"intent": "APPLICATION_UI", "activity_code": "APPLICATION_UI"}

    # Follow-up checks: If user is confirming prerequisites or specifying downtime in an existing session
    from app.core.activity_registry import check_prereq_ack, check_downtime_window
    if check_prereq_ack(text) or check_downtime_window(text):
        if any(k in full_lower for k in ["version", "upgrade", "downgrade", "patch"]):
            return {"intent": "APPLICATION_VERSION", "activity_code": "APPLICATION_VERSION"}
        if any(k in full_lower for k in ["client", "transfer", "migrate"]):
            return {"intent": "CLIENT_DATA_TRANSFER", "activity_code": "CLIENT_DATA_TRANSFER"}
        if any(k in full_lower for k in ["file", "archive", "log", "permission"]):
            return {"intent": "FILE_MANAGEMENT", "activity_code": "FILE_MANAGEMENT"}

    # 8. Out-of-scope non-IT topics check
    has_out_of_scope = any(re.search(rf"\b{re.escape(kw)}\b", full_lower) for kw in OUT_OF_SCOPE_KEYWORDS)
    has_it_keyword = any(re.search(rf"\b{re.escape(kw)}\b", full_lower) for kw in IT_KEYWORDS)
    is_non_it_inquiry = bool(re.search(r"\b(where (can|to|we|i|is|are)|find|best place|places to|how to reach|recommend a|buy a|sell a)\b", full_lower))
    
    if (has_out_of_scope or is_non_it_inquiry) and not has_it_keyword:
        return {"intent": "NON_TECHNICAL", "activity_code": "NON_TECHNICAL"}

    # 9. Application support (real issues with IT keywords)
    if has_it_keyword or any(w in full_lower for w in ["slow", "broken", "issue", "not working", "fails", "down", "glitch", "problem", "downtime", "prerequisite"]):
        return {"intent": "APPLICATION_UI", "activity_code": "APPLICATION_UI"}

    # Default fallback for general IT inquiries
    return {"intent": "general_query", "activity_code": "UNKNOWN"}


def detect_session_active_activity(state: AgentState, user_msg: str, messages: list) -> str:
    """
    Determines if there is an active operational maintenance activity already established
    in the ongoing conversation session.
    """
    # 1. Direct state activity code
    act = state.get("activity_code")
    if act and act not in ["UNKNOWN", "NON_TECHNICAL", "ActivityCode"]:
        return act

    # 2. Check intent if valid
    intent = state.get("intent")
    if intent in [
        "APPLICATION_VERSION", "CLIENT_DATA_TRANSFER", "FILE_MANAGEMENT",
        "APPLICATION_UI", "SERVER", "DATABASE", "NETWORK", "SECURITY", "OTHER_TECHNICAL"
    ]:
        return intent

    # 3. Check extracted fields category
    cat = (state.get("extracted_fields") or {}).get("category", "")
    if "version" in cat.lower():
        return "APPLICATION_VERSION"
    if "client" in cat.lower() or "transfer" in cat.lower():
        return "CLIENT_DATA_TRANSFER"
    if "file" in cat.lower():
        return "FILE_MANAGEMENT"
    if "ui" in cat.lower():
        return "APPLICATION_UI"

    # 4. Check conversation history
    all_user_msgs = [m.get("content", "") for m in messages if m.get("role") == "user"]
    combined = " ".join(all_user_msgs).lower()
    if any(k in combined for k in ["application version", "version upgrade", "upgrade application", "downgrade application", "runtime engine", "version maintenance"]):
        return "APPLICATION_VERSION"
    if any(k in combined for k in ["client data transfer", "transfer data", "client 100", "client 200", "migrate client"]):
        return "CLIENT_DATA_TRANSFER"
    if any(k in combined for k in [
        "file management", "files management", "file mangement", "files mangements",
        "file permission", "file permissions", "permission for the files", "permissions for the files",
        "permission change", "file access", "directory permissions", "housekeeping script", "archive logs"
    ]):
        return "FILE_MANAGEMENT"
    if any(k in combined for k in ["ui change", "button broken", "layout issue"]):
        return "APPLICATION_UI"

    return "UNKNOWN"


async def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    user_msg = state.get("current_user_message", "")
    messages = state.get("messages", [])
    existing_act = state.get("activity_code", "UNKNOWN")
    existing_intent = state.get("intent", "UNKNOWN")

    # Fast deterministic check for greetings and activity overview requests
    if is_greeting_or_activity_overview(user_msg):
        return {
            "intent": "general_query",
            "activity_code": "UNKNOWN",
            "technical_scope": "application",
            "confidence": 1.0,
            "ticket_eligible": False,
            "restricted_operation": False,
            "requires_admin_approval": False,
            "requires_manager_review": False,
        }

    # Fast deterministic check for explicit out-of-scope non-technical queries
    fast_rule = rule_based_intent_fallback(user_msg, messages)
    if fast_rule["intent"] == "NON_TECHNICAL":
        return {
            "intent": "NON_TECHNICAL",
            "activity_code": "NON_TECHNICAL",
            "technical_scope": "non_technical",
            "confidence": 1.0,
            "ticket_eligible": False,
            "restricted_operation": False,
            "requires_admin_approval": False,
            "requires_manager_review": False,
        }

    result = {}

    valid_codes = {
        "APPLICATION_UI", "APPLICATION_VERSION", "CLIENT_DATA_TRANSFER", "FILE_MANAGEMENT",
        "SERVER", "DATABASE", "NETWORK", "SECURITY", "OTHER_TECHNICAL",
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
                if matched_code:
                    result["intent"] = matched_code
                    result["activity_code"] = matched_code if matched_code not in ["ticket_status", "draft_modification", "general_query"] else "UNKNOWN"
                    result["confidence"] = parsed.get("confidence", 0.9)
            except Exception as exc:
                logger.warning("Failed to parse LLM intent classification response: %s", exc)

    if not result:
        res = rule_based_intent_fallback(user_msg, messages)
        result["intent"] = res["intent"]
        result["activity_code"] = res["activity_code"]
        result["confidence"] = 0.8

    # Out-of-scope safety check: if user message is non-technical, strictly enforce NON_TECHNICAL
    rule_res = rule_based_intent_fallback(user_msg, messages)
    if rule_res["intent"] == "NON_TECHNICAL":
        result["intent"] = "NON_TECHNICAL"
        result["activity_code"] = "NON_TECHNICAL"

    # Keyword safety check to prioritize the 4 core Application Activities
    user_lower = user_msg.lower()
    if any(k in user_lower for k in ["upgrade", "downgrade", "version", "patch", "binary", "binaries"]):
        result["intent"] = "APPLICATION_VERSION"
        result["activity_code"] = "APPLICATION_VERSION"
    elif any(k in user_lower for k in ["transfer data", "data migration", "client 100", "client 200", "copy client", "client sync"]):
        result["intent"] = "CLIENT_DATA_TRANSFER"
        result["activity_code"] = "CLIENT_DATA_TRANSFER"
    elif any(k in user_lower for k in [
        "file management", "files management", "file mangement", "files mangements",
        "file permission", "file permissions", "permission for the files", "permissions for the files",
        "permission change", "permissions change", "file access", "directory permissions",
        "archive logs", "housekeeping script", "upload file", "download file"
    ]):
        result["intent"] = "FILE_MANAGEMENT"
        result["activity_code"] = "FILE_MANAGEMENT"
    elif any(k in user_lower for k in ["ui change", "button broken", "layout issue", "form field"]):
        result["intent"] = "APPLICATION_UI"
        result["activity_code"] = "APPLICATION_UI"

    # If an ongoing operational activity was already active in this session, keep it for follow-ups
    # UNLESS the user asks a non-technical or out-of-scope query, or explicit topic change
    ongoing_act = detect_session_active_activity(state, user_msg, messages)
    if ongoing_act not in ["UNKNOWN", "NON_TECHNICAL"] and result.get("intent") != "NON_TECHNICAL":
        explicit_topic_change = bool(re.search(r"\b(what activities|explain activities|activity list|hello|hi|hey|tkt-|leave|salary|hr|cancel|switch to|instead)\b", user_msg.lower()))
        if not explicit_topic_change:
            result["intent"] = ongoing_act
            result["activity_code"] = ongoing_act

    # If user explicitly requests ticket creation in an active session, ensure ticket-eligible routing
    if any(k in user_lower for k in ["create ticket", "open ticket", "raise ticket", "draft ticket", "make a ticket", "prerquities done", "prerequisites done"]):
        if ongoing_act not in ["UNKNOWN", "NON_TECHNICAL"]:
            result["intent"] = ongoing_act
            result["activity_code"] = ongoing_act

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
