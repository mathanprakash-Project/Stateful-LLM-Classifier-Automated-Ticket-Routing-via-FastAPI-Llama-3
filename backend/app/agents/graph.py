"""
LangGraph stateful workflow builder for AI ticket triage & creation.
"""

from typing import Literal
from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    classify_intent_node,
    extract_info_node,
    check_completeness_node,
    generate_draft_node,
    generate_response_node,
)
from app.agents.state import AgentState


def is_informational_query(msg: str) -> bool:
    q = (msg or "").lower().strip()
    from app.core.activity_registry import check_downtime_window
    if check_downtime_window(q) and not any(k in q for k in ["what is", "explain", "why", "how does", "difference"]):
        return False
    return any(k in q for k in [
        "explain", "what is", "what does", "how does", "tell me about", "details of",
        "describe", "alone", "understand", "overview of", "walk me through", "guide on", "meaning of",
        "hybrid mode", "execution mode", "downtime are not", "is downtime", "why do we", "do we need downtime",
        "why downtime", "difference between", "how it works", "what is lockout",
        "step", "steps", "procedure", "how to create", "how do i create"
    ])


def route_by_intent(state: AgentState) -> Literal["extract_info", "generate_response"]:
    user_role = (state.get("user_role") or "user").lower()
    # Non-user roles (Employee, Manager, Admin) use the assistant as an Operational & Technical Advisor
    # They do not create tickets, so we route directly to generate_response to answer their doubts.
    if user_role != "user":
        return "generate_response"

    user_msg = state.get("current_user_message", "")
    if is_informational_query(user_msg):
        return "generate_response"

    intent = state.get("intent", "APPLICATION_UI")
    # Intents that go directly to response generation (no ticket extraction needed)
    skip_extraction_intents = {"NON_TECHNICAL", "out_of_scope", "ticket_status", "general_query"}
    if intent in skip_extraction_intents:
        return "generate_response"
    # All ticket-eligible intents (APPLICATION_UI, APPLICATION_VERSION, etc.) need extraction
    return "extract_info"


def route_completeness(state: AgentState) -> Literal["generate_draft", "generate_response"]:
    user_role = (state.get("user_role") or "user").lower()
    if user_role != "user":
        return "generate_response"

    # Strict safety check:
    # If the activity is APPLICATION_VERSION or CLIENT_DATA_TRANSFER,
    # verify that downtime window is truly present before allowing draft generation!
    act_code = state.get("activity_code") or state.get("intent") or "UNKNOWN"
    cat_name = str((state.get("extracted_fields") or {}).get("category", "")).lower()
    if act_code in ["APPLICATION_VERSION", "CLIENT_DATA_TRANSFER"] or any(k in cat_name for k in ["version", "transfer"]):
        from app.core.activity_registry import check_downtime_window
        messages = state.get("messages") or []
        all_user_text = " ".join([m.get("content", "") for m in messages if m.get("role") == "user"])
        if state.get("current_user_message"):
            all_user_text += " " + state.get("current_user_message")
        if not check_downtime_window(all_user_text):
            return "generate_response"

    missing = state.get("missing_fields", [])
    if not missing:
        return "generate_draft"
    return "generate_response"


def build_ticket_agent_graph():
    builder = StateGraph(AgentState)

    # Register Nodes
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("extract_info", extract_info_node)
    builder.add_node("check_completeness", check_completeness_node)
    builder.add_node("generate_draft", generate_draft_node)
    builder.add_node("generate_response", generate_response_node)

    # Connect Edges
    builder.add_edge(START, "classify_intent")
    builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "extract_info": "extract_info",
            "generate_response": "generate_response",
        },
    )

    builder.add_edge("extract_info", "check_completeness")
    builder.add_conditional_edges(
        "check_completeness",
        route_completeness,
        {
            "generate_draft": "generate_draft",
            "generate_response": "generate_response",
        },
    )

    builder.add_edge("generate_draft", "generate_response")
    builder.add_edge("generate_response", END)

    return builder.compile()


ticket_agent_graph = build_ticket_agent_graph()


async def run_chat_turn(
    session_id: str,
    user_id: str,
    user_name: str,
    user_message: str,
    existing_messages: list[dict],
    current_state: dict,
    user_role: str = "user",
    preferred_model: str | None = None,
) -> dict:
    state_input: AgentState = {
        "session_id": session_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_role": user_role,
        "preferred_model": preferred_model,
        "current_user_message": user_message,
        "messages": existing_messages,
        "intent": current_state.get("intent"),
        "activity_code": current_state.get("activity_code"),
        "extracted_fields": current_state.get("extracted_fields", {}),
        "missing_fields": current_state.get("missing_fields", []),
        "draft": None,
        "draft_id": current_state.get("draft_id"),
        "draft_status": current_state.get("draft_status"),
        "needs_human_approval": False,
        "ticket_created": current_state.get("ticket_created"),
        "response_text": None,
        "error": None,
    }

    result = await ticket_agent_graph.ainvoke(state_input)
    return result

