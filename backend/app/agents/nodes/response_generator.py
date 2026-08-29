"""
Response generator node for conversational feedback, diagnostic questions, and domain guardrail responses.
"""

import json
import logging
from typing import Any, Dict

from app.agents.prompts.system_prompts import (
    DIAGNOSTIC_QUESTION_PROMPT,
    DRAFT_PRESENTATION_PROMPT,
    OUT_OF_SCOPE_RESPONSE_PROMPT,
)
from app.agents.state import AgentState
from app.config.settings import settings
from app.core.llm_client import call_ollama

logger = logging.getLogger(__name__)


async def generate_response_node(state: AgentState) -> Dict[str, Any]:
    """
    Generates a natural, empathetic response for the user, asking follow-up questions,
    handling out-of-scope boundaries, or presenting a prepared draft.
    """
    intent = state.get("intent", "general_query")
    is_complete = state.get("is_complete", False)
    missing = state.get("missing_fields", [])
    extracted = state.get("extracted_fields", {})
    draft_data = state.get("draft")
    messages = state.get("messages", [])

    last_user_msg = state.get("current_user_message", "")
    if not last_user_msg and messages:
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

    # 1. Out-of-scope / non-IT topic handler
    if intent == "out_of_scope":
        if settings.LLM_PROVIDER != "mock":
            prompt = (
                f"{OUT_OF_SCOPE_RESPONSE_PROMPT}\n\n"
                f"User Message: {last_user_msg}\n\n"
                f"Courteous IT Boundary Response in Markdown:"
            )
            llm_reply = await call_ollama(prompt)
            if llm_reply:
                return {"response_text": llm_reply}

        response_text = (
            "I can only assist with **technical IT support issues** (such as computer hardware, software errors, VPN/network connectivity, and account access).\n\n"
            "I cannot create support tickets for personal inquiries, clothing/apparel, or non-technical topics.\n\n"
            "If you are experiencing a technical issue with your work computer, applications, or network, please let me know and I'll be glad to help!"
        )
        return {"response_text": response_text}

    # 2. Ticket status handler
    if intent == "ticket_status":
        response_text = (
            "You can track and check the live progress of all your active tickets directly in the **All Tickets** registry tab on the sidebar. "
            "If you have a specific ticket number (e.g. `TKT-260827-0001`), let me know and I can inspect it for you."
        )
        return {"response_text": response_text}

    # 3. General query / greetings handler
    if intent == "general_query":
        response_text = (
            "👋 **Hello! I'm your AI IT Support Specialist.**\n\n"
            "I can assist you with:\n"
            "- 💻 **Hardware Issues** (Laptops, Monitors, Peripherals, Docking stations)\n"
            "- ⚙️ **Software Problems** (OS crashes, application errors, licenses, installations)\n"
            "- 🌐 **Network & Connectivity** (Wi-Fi, Fiber/Broadband, VPN, Slow internet)\n"
            "- 🔐 **Access & Security** (Password resets, MFA/2FA devices, Permissions)\n\n"
            "How can I help you today? Please describe what technical problem you are experiencing."
        )
        return {"response_text": response_text}

    # 4. If grievance report is complete and draft is prepared
    if is_complete and draft_data:
        title = draft_data.get("title", "Support Request")
        cat = draft_data.get("category_name", "General Support")
        prio = draft_data.get("priority", "medium").upper()
        
        response_text = (
            f"✅ **I have analyzed your issue and prepared an official support ticket draft:**\n\n"
            f"- **Title:** {title}\n"
            f"- **Category:** {cat}\n"
            f"- **Priority:** `{prio}`\n\n"
            f"Please review the draft card below and click **Approve & Create Ticket** to submit it to our support engineering queue."
        )
        return {"response_text": response_text}

    # 5. Otherwise, generate targeted diagnostic follow-up questions
    if settings.LLM_PROVIDER != "mock":
        prompt_content = (
            f"{DIAGNOSTIC_QUESTION_PROMPT}\n\n"
            f"User Message: {last_user_msg}\n"
            f"Extracted info so far: {json.dumps(extracted)}\n"
            f"Missing Details needed: {', '.join(missing)}\n\n"
            f"Helpful Diagnostic Response in Markdown:"
        )
        llm_reply = await call_ollama(prompt_content)
        if llm_reply:
            return {"response_text": llm_reply}

    # Rule-based diagnostic fallback
    issue_topic = extracted.get("category") or "your issue"
    response_text = (
        f"I understand you're experiencing trouble with **{issue_topic}**. To help me accurately diagnose and triage this ticket, could you please clarify:\n\n"
        f"1. **Device / Environment:** What device model or operating system/application are you using?\n"
        f"2. **Impact & Urgency:** Is this completely blocking your daily work or intermittent?\n"
        f"3. **Troubleshooting:** Have you tried any quick steps yet (e.g. restarting, reconnecting cables/router)?"
    )
    return {"response_text": response_text}


response_generator_node = generate_response_node
