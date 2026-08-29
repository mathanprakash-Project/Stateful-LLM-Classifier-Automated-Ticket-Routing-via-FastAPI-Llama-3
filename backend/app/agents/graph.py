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


def route_by_intent(state: AgentState) -> Literal["extract_info", "generate_response"]:
    intent = state.get("intent", "grievance_report")
    if intent in ("grievance_report", "draft_modification"):
        return "extract_info"
    return "generate_response"


def route_completeness(state: AgentState) -> Literal["generate_draft", "generate_response"]:
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
) -> dict:
    state_input: AgentState = {
        "session_id": session_id,
        "user_id": user_id,
        "user_name": user_name,
        "current_user_message": user_message,
        "messages": existing_messages,
        "intent": current_state.get("intent"),
        "extracted_fields": current_state.get("extracted_fields", {}),
        "missing_fields": current_state.get("missing_fields", []),
        "draft": current_state.get("draft"),
        "draft_id": current_state.get("draft_id"),
        "draft_status": current_state.get("draft_status"),
        "needs_human_approval": current_state.get("needs_human_approval", False),
        "ticket_created": current_state.get("ticket_created"),
        "response_text": None,
        "error": None,
    }

    result = await ticket_agent_graph.ainvoke(state_input)
    return result

