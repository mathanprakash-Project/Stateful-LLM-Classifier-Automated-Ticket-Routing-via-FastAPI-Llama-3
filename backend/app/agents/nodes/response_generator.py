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
    MANAGER_ROUTING_RESPONSE_PROMPT,
    RESTRICTED_OPERATION_RESPONSE_PROMPT,
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

    user_role = (state.get("user_role") or "user").lower()

    # 0. Staff Technical Advisor Mode (Employee / Manager / Admin)
    # Staff can chat with the assistant regarding doubts and questions on how to perform activities (zero ticket drafting).
    if user_role != "user":
        if settings.LLM_PROVIDER != "mock":
            staff_prompt = (
                f"You are an Enterprise Operational & Technical Advisor assisting internal IT staff (Role: {user_role.upper()}).\n\n"
                "CRITICAL SYSTEM POLICIES:\n"
                "1. In this system, ONLY requester User profiles create tickets. Internal staff (Employees, Managers, Admins) do NOT create tickets.\n"
                "2. The staff member is asking technical questions, doubts, or operational guidelines on how activities work or how to perform them.\n"
                "3. NEVER provide instructions or steps for Admins, Managers, or Employees to create or submit a ticket.\n"
                "4. Directly explain the technical and operational activity (purpose, execution mode, prerequisites, downtime impact, verification steps, and how employees execute it).\n"
                "5. If the query mentions ticket creation, clarify simply: 'In our system, tickets are created exclusively by customer User profiles. As staff, our role is to review, execute, and resolve these activities.' Then directly explain how the activity is performed.\n"
                "6. Keep your explanation direct, professional, and well-structured in markdown with bullet points.\n\n"
                f"Staff Member Query: {last_user_msg}\n\n"
                "Technical Advisor Response in Markdown:"
            )
            llm_reply = await call_ollama(staff_prompt)
            if llm_reply:
                return {"response_text": llm_reply}

        # Fallback technical guidance if LLM is in mock mode or offline
        from app.core.activity_registry import get_activity
        act_code = state.get("activity_code", intent)
        act_def = get_activity(act_code)
        if act_def:
            prereq_items = "\n".join([f"- {p}" for p in act_def.prerequisites]) if act_def.prerequisites else "- Standard system health check"
            return {
                "response_text": (
                    f"### 🛠️ **Technical Execution Advisory: {act_def.activity_name}** (`{act_def.activity_code}`)\n\n"
                    f"**Execution Mode:** `{act_def.execution_mode}` | **Downtime Requirement:** `{act_def.downtime_description}`\n\n"
                    f"**Summary & Impact:**\n{act_def.customer_impact_summary}\n\n"
                    f"**Prerequisites & Verification Checklist:**\n{prereq_items}\n\n"
                    f"**Execution Guidelines for Employees & Staff:**\n"
                    f"1. **Pre-flight Checks:** Validate database locks, system backup snapshots, and staging verifications.\n"
                    f"2. **Maintenance Execution:** Apply executable binaries, run migration scripts, and clear system caches.\n"
                    f"3. **Post-execution Health:** Verify application endpoints and update the ticket status with operational completion notes."
                )
            }
        return {
            "response_text": (
                "👋 **Employee & Staff Operational Advisor**\n\n"
                "I am here to assist internal staff (Employees, Managers, Admins) with operational guidelines, command procedures, and technical advice for performing activities across our application stack.\n\n"
                "Feel free to ask any questions or doubts regarding **Application Versioning**, **Client Data Transfer**, **File Housekeeping**, **UI adaptations**, or system maintenance procedures."
            )
        }

    # 1. Out-of-scope / non-technical topic handler
    if intent in ("out_of_scope", "NON_TECHNICAL"):
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

    # 3. General query / greetings / activity list handler
    if intent == "general_query":
        response_text = (
            "👋 **Hello! I'm your Enterprise Application Support AI Specialist.**\n\n"
            "### 🛠️ **Operational Maintenance Activities Overview**\n\n"
            "| Activity | Execution Mode | Downtime Required? | Customer Impact & Summary |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **Application Versioning** (`APPLICATION_VERSION`) | Offline | **Yes** (Planned Downtime) | System executables and engine files are locked while running; all services must be stopped to apply core runtime upgrades. *(Requires Admin Approval)* |\n"
            "| **Client Data Transfer** (`CLIENT_DATA_TRANSFER`) | Hybrid | **No Full Downtime** (User Lockout) | System remains powered on, but active users are locked out from target/source environments to avoid data conflicts. *(Requires Admin Approval)* |\n"
            "| **File Management** (`FILE_MANAGEMENT`) | Online | **No Downtime** | Background housekeeping scripts clean, archive, and transfer host files seamlessly while normal business continues. |\n"
            "| **UI Change and Issues** (`APPLICATION_UI`) | Online | **No Downtime** | Screen adaptations, layout enhancements, and UI error fixes deploy directly with zero business disruption. |\n"
            "| **General Support** (`APPLICATION_OTHER`) | Online | **No Downtime** | Daily account access, performance guidance, and feature requests. |\n\n"
            "---\n\n"
            "### 💡 **How Our Operations Work:**\n"
            "- **Application Versioning**: *Think of this as upgrading the engine of a car. Because we are replacing core moving parts, the system must be turned off briefly during the maintenance window.*\n"
            "- **Client Data Transfer**: *The system stays on, but user logins in the target test system are temporarily locked to prevent partial entries from corrupting the transfer.*\n"
            "- **File Management**: *Automated background housekeeping running scheduled archiving scripts with zero user interruption.*\n"
            "- **UI Changes & Issues**: *Screen layout adjustments and error fixes published in real time with instant page refresh.*\n\n"
            "### 🏢 **Out-of-Scope (Infrastructure, Database, Network, Security):**\n"
            "Requests for database modifications, physical server restarts, or corporate firewalls will be reviewed and routed by **Managers** to the appropriate infrastructure engineering teams.\n\n"
            "💬 *Please describe your specific maintenance request or issue, and I will guide you through prerequisites, downtime verification, and ticket drafting!*"
        )
        return {"response_text": response_text}

    # 4. If grievance report is complete and draft is prepared
    if draft_data:
        title = draft_data.get("title", "Support Request")
        cat = draft_data.get("category_name", "General Support")
        prio = draft_data.get("priority", "medium").upper()
        activity = draft_data.get("activity_code", "UNKNOWN")
        restricted = draft_data.get("restricted_operation", False)
        manager_review = draft_data.get("requires_manager_review", False)
        
        response_text = f"✅ **Operational Ticket Draft Prepared:**\n\n"
        response_text += f"- **Title:** {title}\n- **Activity / Category:** {cat} (`{activity}`)\n- **Priority:** `{prio}`\n\n"
        
        if manager_review and activity in ["SERVER", "DATABASE", "NETWORK", "SECURITY", "OTHER_TECHNICAL"]:
            response_text = "This request is outside standard application support and will be routed to the specialized infrastructure team for Manager Review.\n\n" + response_text
        elif restricted:
            response_text = "This is a restricted operational maintenance activity. Please verify the prerequisites and downtime acknowledgment on the draft card below to submit it for Administrator Approval.\n\n" + response_text
        else:
            response_text += "Please review the draft card below, verify prerequisites, and click **Approve & Create Ticket** to send this to the support queue."

        return {"response_text": response_text}

    # 5. Targeted Maintenance Operational Diagnostic (No apologies, direct prerequisite & downtime check)
    from app.core.activity_registry import get_activity
    act_code = state.get("activity_code", intent)
    act_def = get_activity(act_code)

    if act_def and act_def.prerequisites:
        prereq_items = "\n".join([f"- {p}" for p in act_def.prerequisites])
        downtime_info = act_def.downtime_description
        response_text = (
            f"### 🛠️ **{act_def.activity_name} — Prerequisites & Downtime Verification**\n\n"
            f"**Execution Mode:** `{act_def.execution_mode}` | **Downtime Requirement:** `{downtime_info}`\n\n"
            f"**Mandatory Prerequisites Checklist:**\n"
            f"{prereq_items}\n\n"
            f"**Action Required:**\n"
            f"1. **Prerequisites Status:** Have all of the above prerequisites been completed and verified? *(If any prerequisite is pending, please complete it before proceeding.)*\n"
            f"2. **Downtime / Maintenance Window:** Please specify your approved maintenance window (date/time) for this operation."
        )
        return {"response_text": response_text}

    # 6. Standard Diagnostic Questions for general issues
    if settings.LLM_PROVIDER != "mock":
        prompt_content = (
            f"{DIAGNOSTIC_QUESTION_PROMPT}\n\n"
            f"User Message: {last_user_msg}\n"
            f"Extracted info so far: {json.dumps(extracted)}\n"
            f"Missing Details needed: {', '.join(missing)}\n\n"
            f"Helpful Diagnostic Response in Markdown (DO NOT APOLOGIZE):"
        )
        llm_reply = await call_ollama(prompt_content)
        if llm_reply:
            return {"response_text": llm_reply}

    # Rule-based diagnostic fallback
    issue_topic = extracted.get("category") or "your issue"
    response_text = (
        f"Regarding **{issue_topic}**, please provide the following operational details:\n\n"
        f"1. **Environment:** What application version or client environment is affected?\n"
        f"2. **Impact:** Is this completely blocking or scheduled maintenance?\n"
        f"3. **Steps Taken:** What specific actions or error codes were encountered?"
    )
    return {"response_text": response_text}


response_generator_node = generate_response_node
