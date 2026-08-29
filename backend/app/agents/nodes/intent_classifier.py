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
from app.core.llm_client import call_ollama

logger = logging.getLogger(__name__)

# Non-IT keywords that indicate out-of-scope requests
OUT_OF_SCOPE_KEYWORDS = [
    "pant", "pants", "cargo", "jeans", "shirt", "tshirt", "t-shirt", "dress", "clothes", "clothing",
    "shoe", "shoes", "wear", "zudio", "zara", "h&m", "fabric", "tailor", "tight", "loose",
    "food", "pizza", "burger", "coffee", "lunch", "dinner", "recipe", "cook", "hungry",
    "movie", "song", "lyrics", "cricket", "football", "match", "joke", "funny", "dating", "love",
    "medical", "doctor", "headache", "fever", "medicine", "pill", "hospital"
]

# Explicit IT / Technical keywords
IT_KEYWORDS = [
    "laptop", "desktop", "computer", "macbook", "dell", "lenovo", "thinkpad", "screen", "monitor",
    "keyboard", "mouse", "printer", "scanner", "dock", "hdmi", "charger", "battery", "usb",
    "wifi", "wi-fi", "internet", "network", "vpn", "router", "broadband", "airfiber", "fiber", "ethernet",
    "dns", "ip", "ping", "mbps", "gbps", "speed", "unstable", "disconnect", "connection",
    "software", "app", "application", "crash", "error", "bug", "freeze", "windows", "linux", "macos",
    "install", "update", "license", "excel", "outlook", "teams", "slack", "chrome", "browser",
    "password", "login", "locked", "mfa", "2fa", "access", "permission", "account", "auth",
    "ticket", "tkt-", "support", "billing", "invoice", "charge", "refund", "subscription"
]


def rule_based_intent_fallback(text: str) -> str:
    lower = text.lower().strip()
    
    # 1. Check ticket status queries
    if any(k in lower for k in ["tkt-", "status of", "ticket status", "check ticket", "track ticket"]):
        return "ticket_status"
    
    # 2. Check draft modifications
    if any(k in lower for k in ["change priority", "update draft", "edit title", "modify draft", "change category"]):
        return "draft_modification"
    
    # 3. Check casual greetings
    if any(k in lower for k in ["hello", "hi", "hey", "good morning", "good afternoon", "who are you", "what can you do"]):
        if len(text.split()) <= 4:
            return "general_query"
    
    # 4. Out-of-scope non-IT topics check
    # If it contains out-of-scope words and does NOT contain any IT keywords
    has_out_of_scope = any(re.search(rf"\b{re.escape(kw)}\b", lower) for kw in OUT_OF_SCOPE_KEYWORDS)
    has_it_keyword = any(re.search(rf"\b{re.escape(kw)}\b", lower) for kw in IT_KEYWORDS)
    
    if has_out_of_scope and not has_it_keyword:
        return "out_of_scope"

    # 5. Legitimate IT grievance check
    if has_it_keyword or any(w in lower for w in ["slow", "broken", "issue", "not working", "fails", "down", "glitch"]):
        return "grievance_report"

    # If ambiguous and short / non-technical, avoid creating unwanted ticket drafts
    if len(text.split()) < 4:
        return "general_query"

    return "out_of_scope"


async def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    user_msg = state.get("current_user_message", "")

    if settings.LLM_PROVIDER != "mock":
        prompt = f"{INTENT_CLASSIFIER_PROMPT}\n\nUser Message: {user_msg}\n\nJSON Output:"
        response = await call_ollama(prompt, format_json=True)
        if response:
            try:
                parsed = json.loads(response)
                intent = parsed.get("intent")
                if intent in ("grievance_report", "out_of_scope", "ticket_status", "draft_modification", "general_query"):
                    return {"intent": intent}
            except Exception as exc:
                logger.warning("Failed to parse LLM intent classification response: %s", exc)

    # Fallback to rules
    intent = rule_based_intent_fallback(user_msg)
    return {"intent": intent}
