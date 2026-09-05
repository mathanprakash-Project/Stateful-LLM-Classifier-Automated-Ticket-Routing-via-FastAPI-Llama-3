"""
Response generator node for conversational feedback, diagnostic questions, and domain guardrail responses.
"""

import json
import logging
from typing import Any, Dict, Optional

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

from app.core.activity_registry import (
    get_activity,
    ActivityDefinition,
    ACTIVITY_REGISTRY,
    SUPPORT_TEAM_ACTIVITIES_OVERVIEW_RESPONSE,
    is_greeting_or_activity_overview,
    check_prereq_ack,
    check_downtime_window,
    is_prereq_explicitly_pending,
)

logger = logging.getLogger(__name__)

SUPPORT_TEAM_OUT_OF_SCOPE_RESPONSE = (
    "Thank you for reaching out to SupportHub AI. We are happy to assist you with any technical issues related to our application. "
    "However, we want to politely inform you that our support system is not configured to provide information on non-technical topics "
    "such as personal inquiries, food recommendations, or places to visit.\n\n"
    "As the Enterprise Application Support Team, we are strictly focused on assisting with technical application maintenance and operations. "
    "Our team is equipped to help with the following activities:\n\n"
    "- **Application UI Maintenance** (Online, No Downtime)\n"
    "- **File Management Operations** (Online, No Downtime)\n"
    "- **Client Data Transfer** (Hybrid, User Lockout)\n"
    "- **Application Version Maintenance** (Offline, Planned Downtime)\n\n"
    "If you are experiencing any issues with our application, such as difficulties with file management or data transfer, we would be happy to help you troubleshoot or resolve the issue. "
    "Alternatively, if you have any questions about application UI maintenance or version updates, we would be more than happy to assist you.\n\n"
    "Please let us know how we can help with any technical application-related matters, and we will do our best to provide a solution.\n\n"
    "Best regards,  \n"
    "**Enterprise Application Support Team**  \n"
    "SupportHub AI"
)


def detect_specific_activity_in_query(query: str) -> Optional[str]:
    q = (query or "").lower().strip()
    # 1. Client Data Transfer
    if any(k in q for k in ["client transfer data", "client data transfer", "data transfer", "transfer data", "client transfer", "data sync", "replicate data", "client-to-client", "client 100", "client 200"]):
        return "CLIENT_DATA_TRANSFER"
    # 2. Application Versioning
    if any(k in q for k in ["versioning", "application version", "version upgrade", "version maintenance", "runtime engine", "version downgrade", "core binary", "core upgrade"]):
        return "APPLICATION_VERSION"
    # 3. File Management
    if any(k in q for k in ["file management", "file upload", "housekeeping script", "log archive", "file processing", "file replacement", "archive script"]):
        return "FILE_MANAGEMENT"
    # 4. UI Change and Issues
    if any(k in q for k in ["ui change", "ui issue", "ui activity", "screen layout", "ui bug", "ui error", "broken button", "frontend bug", "layout problem"]):
        return "APPLICATION_UI"
    # 5. General Support / Application Screen Issues
    if any(k in q for k in ["general support", "application support", "login issue", "account access"]):
        return "APPLICATION_UI"
    # 6. Database
    if any(k in q for k in ["database", "dba", "db connection", "db storage", "sql issue"]):
        return "DATABASE"
    # 7. Server / Infrastructure
    if any(k in q for k in ["server", "infrastructure", "cpu issue", "memory issue", "server down", "reboot server"]):
        return "SERVER"
    # 8. Network
    if any(k in q for k in ["network", "vpn", "firewall", "dns", "bandwidth"]):
        return "NETWORK"
    # 9. Security
    if any(k in q for k in ["security", "infosec", "access violation", "vulnerability", "audit"]):
        return "SECURITY"
    return None


def is_explanation_request_query(query: str) -> bool:
    q = (query or "").lower().strip()
    explanation_keywords = [
        "explain", "what is", "what does", "how does", "tell me about", "details of",
        "describe", "alone", "understand", "overview of", "walk me through", "guide on", "meaning of"
    ]
    return any(k in q for k in explanation_keywords)


def handle_conceptual_and_operational_inquiry(
    query: str, 
    conversation_history: list[dict], 
    current_activity: Optional[str] = None
) -> Optional[str]:
    q = (query or "").lower().strip()

    # If the user is specifying a maintenance window / schedule, this is NOT a conceptual inquiry
    if check_downtime_window(query) and not any(k in q for k in ["what is", "explain", "why", "how does", "difference"]):
        return None
    
    # 1. Execution Mode & Downtime inquiries
    is_hybrid_query = any(k in q for k in ["what is hybrid", "explain hybrid", "about hybrid", "how does hybrid", "why hybrid", "hybrid mode explained"])
    is_offline_query = any(k in q for k in ["what is offline", "explain offline", "about offline", "how does offline", "why offline", "offline mode explained"])
    is_online_query = any(k in q for k in ["what is online", "explain online", "about online", "how does online", "why online", "online mode explained"])
    is_exec_mode_query = any(k in q for k in ["execution mode", "execution modes", "types of execution"])
    is_downtime_query = any(k in q for k in ["is downtime required", "do we need downtime", "why downtime", "downtime policy", "downtime policies", "what is downtime", "explain downtime", "downtime are not"])

    if is_hybrid_query or (is_exec_mode_query and "hybrid" in q) or (is_downtime_query and ("hybrid" in q or "client" in q or "transfer" in q)):
        return (
            "### 🔄 **Understanding Hybrid Execution Mode & Downtime Policy**\n\n"
            "In our enterprise application support platform, **Hybrid Execution Mode** (used for **Client Data Transfer**) balances operational safety with high system availability.\n\n"
            "#### 1. ❓ **Do We Need Full Downtime in Hybrid Mode?**\n"
            "> **Short Answer:** **NO Full System Downtime is required.**\n>\n"
            "> The physical application servers, backend services, and database engines **remain powered on and running** throughout the entire operation.\n\n"
            "#### 2. 🔒 **What is 'User Lockout' (Why is it needed)?**\n"
            "- While the overall system stays on, active user logins in the **participating / target environments are temporarily locked**.\n"
            "- **Why?** When transferring or replicating master configurations and transactional records between environments, allowing active users to simultaneously enter transactions would create dirty writes, race conditions, or partial data corruption.\n"
            "- Locking user logins ensures the data transfer completes cleanly with 100% data integrity without taking down the underlying infrastructure.\n\n"
            "#### 3. ⚖️ **Execution Mode Comparison:**\n"
            "| Execution Mode | Full Server Downtime? | User Login Lockout? | Primary Example Activity |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **Offline** | **YES (Mandatory)** | Full System Halted | **Application Versioning** (Core executables replaced) |\n"
            "| **Hybrid** | **NO** | **YES (Target Lockout)** | **Client Data Transfer** (Bulk record migration) |\n"
            "| **Online** | **NO** | **NO** | **File Management & UI Changes** (Live background execution) |\n\n"
            "---\n"
            "💬 *Would you like to schedule a Client Data Transfer, or do you have any questions about prerequisites and maintenance windows?*"
        )

    if is_offline_query or (is_exec_mode_query and "offline" in q):
        return (
            "### 🛑 **Understanding Offline Execution Mode**\n\n"
            "**Offline Execution Mode** requires a **Planned Downtime Maintenance Window**.\n\n"
            "#### 1. ❓ **Why is Full Downtime Required?**\n"
            "- In operations like **Application Versioning (`APPLICATION_VERSION`)**, the core runtime binaries, background engines, and system executable files are actively being replaced.\n"
            "- Operating systems lock executable files that are actively running in memory. Therefore, all application services must be gracefully halted during the maintenance window so the new version binaries can be safely swapped in.\n\n"
            "#### 2. 📋 **Mandatory Requirements:**\n"
            "- An **approved maintenance window** (date & time) scheduled in advance.\n"
            "- Verified global directory backups prior to stopping services.\n"
            "- **Administrator Approval** to initiate execution.\n\n"
            "---\n"
            "💬 *If you need to plan a version upgrade or patch, let me know your target version and maintenance schedule!*"
        )

    if is_online_query or (is_exec_mode_query and "online" in q):
        return (
            "### 🟢 **Understanding Online Execution Mode**\n\n"
            "**Online Execution Mode** runs with **Zero Downtime and Zero User Interruption**.\n\n"
            "#### 1. ❓ **How It Works:**\n"
            "- The entire application, database, and all user sessions remain 100% live and accessible.\n"
            "- Activities like **File Management** (background script execution, archiving, cleanup) and **UI Changes & Fixes** (CSS styling, field adjustments) deploy dynamically in the background.\n"
            "- Users immediately see changes upon their next page load without restarting any services.\n\n"
            "---\n"
            "💬 *Do you have a file housekeeping task or UI change you'd like to request?*"
        )

    if is_exec_mode_query:
        return (
            "### ⚙️ **Enterprise Execution Modes Overview**\n\n"
            "Our application operations use 3 distinct execution modes tailored to system safety:\n\n"
            "1. **Offline Mode (`APPLICATION_VERSION`):**\n"
            "   - **Downtime:** Full Planned Downtime Required.\n"
            "   - **Reason:** Core runtime engine files and executables are being replaced.\n\n"
            "2. **Hybrid Mode (`CLIENT_DATA_TRANSFER`):**\n"
            "   - **Downtime:** No full server downtime, but requires a temporary **User Login Lockout** on target systems.\n"
            "   - **Reason:** Prevents concurrent write conflicts while migrating database records.\n\n"
            "3. **Online Mode (`FILE_MANAGEMENT`, `APPLICATION_UI`):**\n"
            "   - **Downtime:** Zero Downtime.\n"
            "   - **Reason:** Background scripts and interface styling apply cleanly with continuous business operations.\n\n"
            "---\n"
            "💬 *Let me know if you would like more details on any specific mode or activity!*"
        )

    if is_downtime_query:
        return (
            "### ⏱️ **Downtime & Maintenance Window Policies**\n\n"
            "Here is the downtime requirement breakdown for application support activities:\n\n"
            "- **Application Versioning (`APPLICATION_VERSION`):** **YES — Planned Downtime Required.** All services must be temporarily stopped to replace core engine executables.\n"
            "- **Client Data Transfer (`CLIENT_DATA_TRANSFER`):** **NO Full Downtime**, but **User Lockout is required** on the target test environment during the transfer window to prevent data corruption.\n"
            "- **File Management (`FILE_MANAGEMENT`):** **NO Downtime.** Scheduled scripts execute in the background.\n"
            "- **UI Changes & Issues (`APPLICATION_UI`):** **NO Downtime.** Interface enhancements and fixes deploy live.\n\n"
            "---\n"
            "💬 *Which operational activity are you planning? Let me know and I will guide you through the exact requirements!*"
        )

    return None


def format_single_activity_comprehensive_explanation(act: ActivityDefinition) -> str:
    approval_text = "Yes (Requires Administrator Approval)" if act.requires_admin_approval else "Direct to Support Agent Queue"
    if act.requires_manager_review:
        approval_text = "Manager Review & Specialized Infrastructure Routing"

    prereqs = ""
    if act.prerequisites:
        prereqs = "\n".join([f"- {p}" for p in act.prerequisites])
    else:
        prereqs = "- Standard operational verification and system access authorization."

    risk_block = ""
    if act.risk_warning and act.risk_warning != "None.":
        risk_block = f"\n\n> ⚠️ **Operational Risk Notice:** {act.risk_warning}"

    text = (
        f"### 🛠️ **{act.activity_name}** (`{act.activity_code}`)\n\n"
        f"**Activity Overview:**\n{act.description}\n\n"
        f"| Operational Property | Specification |\n"
        f"| :--- | :--- |\n"
        f"| **Execution Mode** | `{act.execution_mode}` |\n"
        f"| **Downtime Requirement** | `{act.downtime_description}` |\n"
        f"| **Technical Scope** | `{act.technical_scope.replace('_', ' ').title()}` |\n"
        f"| **Responsible Team** | `{act.responsible_team.replace('_', ' ')}` |\n"
        f"| **Approval Workflow** | `{approval_text}` |\n\n"
        f"### 💡 **How This Activity Works (Plain English):**\n"
        f"{act.customer_analogy}\n\n"
        f"### 📋 **Customer & System Impact:**\n"
        f"{act.customer_summary}\n\n"
        f"### 📋 **Mandatory Prerequisites Checklist:**\n"
        f"{prereqs}"
        f"{risk_block}\n\n"
        f"---\n\n"
        f"💬 *If you would like to proceed with a **{act.activity_name}** request, please confirm that your prerequisites are met and provide your environment details to draft your ticket!*"
    )
    return text


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
    preferred_model = state.get("preferred_model")

    # Format multi-turn conversation history for context
    history_lines = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if content and content != last_user_msg:
            history_lines.append(f"{role.capitalize()}: {content}")
    history_text = "\n".join(history_lines[-8:])

    # 0. If ticket draft is prepared, present it immediately
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

    # Fast-path: If user is asking for activity overview or greeting (and not a single targeted activity)
    target_act_code = detect_specific_activity_in_query(last_user_msg)
    if is_greeting_or_activity_overview(last_user_msg) and not target_act_code:
        return {"response_text": SUPPORT_TEAM_ACTIVITIES_OVERVIEW_RESPONSE}

    # 1. Check if the query is a conceptual / operational question (Execution Mode, Hybrid, Downtime, Lockout, etc.)
    conceptual_reply = handle_conceptual_and_operational_inquiry(last_user_msg, messages, state.get("activity_code"))
    if conceptual_reply:
        if settings.LLM_PROVIDER != "mock":
            llm_prompt = (
                "You are SupportHub AI, an expert Enterprise Application Support Specialist.\n"
                "The user is asking an operational or conceptual question about system execution modes or downtime policies.\n\n"
                f"Conversation History:\n{history_text if history_text else 'None'}\n\n"
                f"User Question: {last_user_msg}\n\n"
                "Answer thoroughly, accurately, conversationally, and friendly in clean Markdown with bullet points. Explain why hybrid needs user lockout without full server downtime."
            )
            llm_res = await call_ollama(llm_prompt, preferred_model=preferred_model)
            if llm_res:
                return {"response_text": llm_res}
        return {"response_text": conceptual_reply}

    # 2. Targeted check: Did the user ask to explain a single specific activity?
    is_explain_query = is_explanation_request_query(last_user_msg)

    if target_act_code and (is_explain_query or "alone" in last_user_msg.lower()):
        act_def = get_activity(target_act_code)
        if act_def:
            if settings.LLM_PROVIDER != "mock":
                single_act_prompt = (
                    f"You are an Enterprise Application Support AI Specialist.\n"
                    f"The user has asked specifically to explain the activity: '{act_def.activity_name}' ({act_def.activity_code}).\n\n"
                    f"Conversation History:\n{history_text if history_text else 'None'}\n\n"
                    f"User Question: {last_user_msg}\n\n"
                    f"CRITICAL INSTRUCTIONS:\n"
                    f"1. Explain ONLY this single activity ({act_def.activity_name}) completely and in detail.\n"
                    f"2. DO NOT output the full overview table of other activities.\n"
                    f"3. Cover Definition, Execution Mode ({act_def.execution_mode}), Downtime Requirement ({act_def.downtime_description}), Plain English Analogy, Prerequisites, and Risk Notice.\n\n"
                    f"Response in clean Markdown:"
                )
                llm_reply = await call_ollama(single_act_prompt, preferred_model=preferred_model)
                if llm_reply:
                    return {"response_text": llm_reply}
            return {"response_text": format_single_activity_comprehensive_explanation(act_def)}

    # 0. Staff Technical Advisor Mode (Employee / Manager / Admin)
    if user_role != "user":
        if settings.LLM_PROVIDER != "mock":
            staff_prompt = (
                f"You are an Enterprise Operational & Technical Advisor assisting internal IT staff (Role: {user_role.upper()}).\n\n"
                "CRITICAL SYSTEM POLICIES:\n"
                "1. In this system, ONLY requester User profiles create tickets. Internal staff (Employees, Managers, Admins) do NOT create tickets.\n"
                "2. The staff member is asking technical questions, doubts, or operational guidelines on how activities work or how to perform them.\n"
                "3. NEVER provide instructions or steps for Admins, Managers, or Employees to create or submit a ticket.\n"
                "4. Directly explain the technical and operational activity (purpose, execution mode, prerequisites, downtime impact, verification steps, and how employees execute it).\n\n"
                f"Conversation History:\n{history_text if history_text else 'None'}\n\n"
                f"Staff Member Query: {last_user_msg}\n\n"
                "Technical Advisor Response in Markdown:"
            )
            llm_reply = await call_ollama(staff_prompt)
            if llm_reply:
                return {"response_text": llm_reply}

        # Fallback technical guidance if LLM is in mock mode or offline
        act_code = target_act_code or state.get("activity_code", intent)
        act_def = get_activity(act_code)
        if act_def:
            prereq_items = "\n".join([f"- {p}" for p in act_def.prerequisites]) if act_def.prerequisites else "- Standard system health check"
            return {
                "response_text": (
                    f"### 🛠️ **Technical Execution Advisory: {act_def.activity_name}** (`{act_def.activity_code}`)\n\n"
                    f"**Execution Mode:** `{act_def.execution_mode}` | **Downtime Requirement:** `{act_def.downtime_description}`\n\n"
                    f"**Summary & Impact:**\n{act_def.customer_impact_summary if hasattr(act_def, 'customer_impact_summary') else act_def.customer_summary}\n\n"
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

    # 1. Out-of-scope / non-technical topic handler (Standardized Enterprise Support Team response)
    if intent in ("out_of_scope", "NON_TECHNICAL"):
        return {"response_text": SUPPORT_TEAM_OUT_OF_SCOPE_RESPONSE}

    # 2. Ticket status handler
    if intent == "ticket_status":
        response_text = (
            "You can track and check the live progress of all your active tickets directly in the **All Tickets** registry tab on the sidebar. "
            "If you have a specific ticket number (e.g. `TKT-260827-0001`), let me know and I can inspect it for you."
        )
        return {"response_text": response_text}

    # 3. General query / greetings / activity list handler
    if intent == "general_query":
        # Check if this query is a follow-up or conceptual question about a single activity
        if target_act_code:
            act_def = get_activity(target_act_code)
            if act_def:
                return {"response_text": format_single_activity_comprehensive_explanation(act_def)}

        # Check if user message is a greeting or inquiry about what we support / activity overview
        if is_greeting_or_activity_overview(last_user_msg):
            return {"response_text": SUPPORT_TEAM_ACTIVITIES_OVERVIEW_RESPONSE}

        # If it's a follow up turn (history exists), call dynamic LLM response rather than static greeting
        if len(messages) > 1 and settings.LLM_PROVIDER != "mock":
            dynamic_prompt = (
                "You are an expert Enterprise Application Support AI Specialist.\n"
                f"Conversation History:\n{history_text}\n\n"
                f"User Message: {last_user_msg}\n\n"
                "Respond directly and conversationally to the user in a helpful, professional tone."
            )
            llm_res = await call_ollama(dynamic_prompt)
            if llm_res:
                return {"response_text": llm_res}

        # Any other general query defaults to the activities overview
        return {"response_text": SUPPORT_TEAM_ACTIVITIES_OVERVIEW_RESPONSE}

    # 5. Targeted Maintenance Operational Diagnostic (Interactive prerequisite & downtime checks)
    act_code = state.get("activity_code", intent)
    act_def = get_activity(act_code)

    if act_def and act_def.prerequisites:
        is_prereq_missing = "prerequisites_status" in missing
        is_window_missing = "maintenance_window" in missing
        prereq_items = "\n".join([f"- {p}" for p in act_def.prerequisites])
        downtime_info = act_def.downtime_description

        # Check if user explicitly stated prerequisites are pending / not yet done
        if is_prereq_explicitly_pending(last_user_msg):
            return {
                "response_text": (
                    f"⚠️ **Prerequisites Pending for {act_def.activity_name}**\n\n"
                    f"Because **{act_def.activity_name}** operates in **{act_def.execution_mode} Mode** ({downtime_info}), all prerequisites must be completed before performing maintenance to avoid system or database conflicts.\n\n"
                    f"**Mandatory Prerequisites Checklist:**\n{prereq_items}\n\n"
                    f"👉 *Please complete the pending items. Once verified, confirm here and let us know your approved maintenance window so we can generate your ticket draft!*"
                )
            }

        # Case A: Prerequisites are confirmed, but Maintenance Window / Downtime is still needed
        if not is_prereq_missing and is_window_missing:
            mode_desc = "Planned Downtime Required" if act_def.execution_mode == "Offline" else "User Lockout Required"
            response_text = (
                f"✅ **Prerequisites Verified & Confirmed!**\n\n"
                f"Great, all prerequisites for **{act_def.activity_name}** are confirmed.\n\n"
                f"Because this operation runs in **{act_def.execution_mode} Mode** (`{mode_desc}`), we need your scheduled downtime/maintenance window before drafting the ticket for Administrator Approval.\n\n"
                f"Thank you for confirming that all prerequisites for **{act_def.activity_name}** are complete and verified. Now, let's move forward with scheduling your maintenance window.\n\n"
                f"Because this operation runs in **{act_def.execution_mode} Mode** (`{mode_desc}`), we need your scheduled maintenance window before drafting the ticket for Administrator Approval.\n\n"
                f"⏱️ **Action Required:**\n"
                f"Please specify your **approved Downtime / Maintenance Window** (Date & Time) for this operation "
                f"(e.g., *'Saturday 10:00 PM to 2:00 AM UTC'* or *'Tomorrow at 11:00 PM'*)."
                f"Please specify your **approved Downtime / Maintenance Window** in the following format:\n"
                f"- **Format:** `DD/MM/YYYY HH:MM to HH:MM (Timezone)`\n"
                f"- **Examples:** `15/09/2026 22:00 to 02:00 UTC` or `15/09/2026 10:00 PM to 02:00 AM IST`\n\n"
                f"Once provided, our team will immediately prepare your official ticket draft!"
            )
            return {"response_text": response_text}

        # Case B: Maintenance Window is specified, but Prerequisites confirmation is still needed
        if is_prereq_missing and not is_window_missing:
            response_text = (
                f"⏱️ **Maintenance Window Noted!**\n\n"
                f"Thank you for providing your scheduled maintenance timeframe.\n\n"
                f"Before we can generate your ticket draft for **{act_def.activity_name}**, please verify the mandatory prerequisites:\n\n"
                f"**Mandatory Prerequisites Checklist:**\n{prereq_items}\n\n"
                f"📋 **Action Required:**\n"
                f"Have all of the above prerequisites been completed and verified? *(Please reply to confirm so we can draft your ticket.)*"
            )
            return {"response_text": response_text}

        # Case C: Initial turn - Neither is confirmed yet, present full overview and checklist
        if act_def.execution_mode in ["Offline", "Hybrid"]:
            action_req = (
                f"**Action Required:**\n"
                f"1. **Prerequisites Status:** Have all of the above prerequisites been completed and verified? *(If any prerequisite is pending, please complete it before proceeding.)*\n"
                f"2. **Downtime / Maintenance Window:** Please specify your approved maintenance window (date/time) for this operation."
                f"2. **Downtime / Maintenance Window:** Please specify your approved maintenance window in the format `DD/MM/YYYY HH:MM to HH:MM (Timezone)` (e.g., `15/09/2026 22:00 to 02:00 UTC` or `15/09/2026 10:00 PM to 02:00 AM IST`)."
            )
            heading_title = f"### 🛠️ **{act_def.activity_name} — Prerequisites & Maintenance Window Verification**\n\n"
        else:
            action_req = (
                f"**Action Required:**\n"
                f"1. **Prerequisites Status:** Have all of the above prerequisites been completed and verified? *(Please confirm if you are ready to proceed with this online activity.)*"
            )
            heading_title = f"### 🛠️ **{act_def.activity_name} — Prerequisites Verification**\n\n"

        response_text = (
            f"{heading_title}"
            f"**Execution Mode:** `{act_def.execution_mode}` | **Downtime Requirement:** `{downtime_info}`\n\n"
            f"**Mandatory Prerequisites Checklist:**\n"
            f"{prereq_items}\n\n"
            f"{action_req}"
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
