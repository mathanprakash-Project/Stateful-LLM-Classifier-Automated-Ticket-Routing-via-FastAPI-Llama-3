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


def rule_based_extraction_fallback(text: str, current_fields: Dict[str, Any]) -> Dict[str, Any]:
    extracted = dict(current_fields or {})
    lower = text.lower()

    # If the user input is out-of-scope noise, do NOT pollute technical fields
    if is_text_out_of_scope(text) and not any(w in lower for w in ["wifi", "airfiber", "vpn", "laptop", "pc", "network", "internet"]):
        return extracted

    # Category heuristic
    if any(w in lower for w in ["vpn", "wifi", "wi-fi", "internet", "dns", "network", "connect", "airfiber", "fiber", "router", "mbps", "bandwidth"]):
        extracted["category"] = "Network"
        if "vpn" in lower:
            extracted["subcategory"] = "VPN Connection"
        elif any(w in lower for w in ["airfiber", "fiber", "broadband", "unstable", "speed", "mbps"]):
            extracted["subcategory"] = "Slow Internet"
        elif "wifi" in lower or "wi-fi" in lower:
            extracted["subcategory"] = "Wi-Fi Connectivity"
    elif any(w in lower for w in ["laptop", "screen", "monitor", "mouse", "keyboard", "printer", "hardware", "dock", "dell", "macbook", "lenovo"]):
        extracted["category"] = "Hardware"
        if "laptop" in lower or "slow" in lower or "fans" in lower:
            extracted["subcategory"] = "Laptop Issue"
        elif "monitor" in lower or "screen" in lower or "hdmi" in lower:
            extracted["subcategory"] = "Monitor / Display"
    elif any(w in lower for w in ["password", "login", "locked", "mfa", "2fa", "access", "permission"]):
        extracted["category"] = "Access & Security"
        if "password" in lower:
            extracted["subcategory"] = "Password Reset"
        elif "locked" in lower:
            extracted["subcategory"] = "Account Locked"
    elif any(w in lower for w in ["charge", "invoice", "refund", "billing", "payment", "subscription", "dollar", "$"]):
        extracted["category"] = "Billing & Payments"
        if "double" in lower or "twice" in lower:
            extracted["subcategory"] = "Double Charge"
        elif "refund" in lower:
            extracted["subcategory"] = "Refund Request"
    elif any(w in lower for w in ["software", "crash", "install", "app", "error", "bug", "license"]):
        extracted["category"] = "Software"
        if "crash" in lower:
            extracted["subcategory"] = "Application Crash"
        elif "install" in lower:
            extracted["subcategory"] = "Software Installation"

    # Priority heuristic
    if any(w in lower for w in ["urgent", "critical", "outage", "blocker", "emergency"]):
        extracted["priority"] = "critical"
    elif any(w in lower for w in ["high priority", "asap", "can't work", "cannot work", "deadline", "unstable", "completely blocks"]):
        extracted["priority"] = "high"
    elif any(w in lower for w in ["low priority", "minor", "whenever"]):
        extracted["priority"] = "low"
    elif "priority" not in extracted:
        extracted["priority"] = "medium"

    # Metadata heuristics
    if any(w in lower for w in ["dell", "macbook", "lenovo", "thinkpad", "windows", "macos", "linux", "airfiber", "airtel", "router"]):
        extracted["affected_system"] = text.strip()
    if any(w in lower for w in ["tried", "reboot", "restarting", "cable", "reset", "attempted", "reconnected", "hdmi"]):
        extracted["troubleshooting_tried"] = text.strip()

    # Title formulation (clean technical summary)
    if "airfiber" in lower or "airtel" in lower:
        extracted["title"] = "Airtel AirFiber Unstable Connection"
    elif not extracted.get("title") or is_text_out_of_scope(extracted.get("title", "")):
        extracted["title"] = text[:60].strip().capitalize()
        if len(text) > 60:
            extracted["title"] += "..."
    
    # Description formulation
    if not extracted.get("description") or is_text_out_of_scope(extracted.get("description", "")):
        extracted["description"] = text.strip()
    else:
        # Append additional technical info if not already included
        if text.strip() not in extracted["description"] and not is_text_out_of_scope(text):
            extracted["description"] = f"{extracted['description']}\nAdditional details: {text.strip()}"

    return extracted


async def extract_info_node(state: AgentState) -> Dict[str, Any]:
    current_fields = state.get("extracted_fields", {})
    user_msg = state.get("current_user_message", "")
    
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

    extracted = rule_based_extraction_fallback(user_msg, current_fields)
    return {"extracted_fields": extracted}
