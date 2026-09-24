"""
LangGraph stateful workflow builder for AI ticket triage & creation.

Evolution Plan v2.0 — 8-node pipeline:
  classify_intent → extract_info → retrieve_context → check_completeness
  → generate_draft → [consensus_validation] → generate_response → rai_guard → END

New nodes (Modules 1, 3, 6):
  - retrieve_context: Hybrid RAG (pgvector + BM25 + RRF) for knowledge-grounded answers
  - consensus_validation: 3-agent majority vote for restricted operations only
  - rai_guard: Deterministic + LLM safety gate (PII, promises, compliance)
"""

from typing import Literal
from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    classify_intent_node,
    extract_info_node,
    check_completeness_node,
    generate_draft_node,
    generate_response_node,
    retrieve_context_node,
    consensus_validation_node,
    rai_guard_node,
)
from app.agents.state import AgentState


def is_informational_query(msg: str) -> bool:
    q = (msg or "").lower().strip()
    from app.core.activity_registry import check_downtime_window
    if check_downtime_window(q) and not any(k in q for k in ["what is", "explain", "why", "how does", "difference", "right", "?"]):
        return False

    # Questions or confirmation queries about downtime, lockout, modes, server, or prerequisites
    if "?" in q or any(k in q for k in ["right", "correct", "true"]):
        if any(k in q for k in [
            "downtime", "lockout", "lock", "offline", "online", "hybrid", "server",
            "mode", "window", "prerequisite", "prerequisites", "data", "why", "what",
            "how", "will", "can", "does", "is it", "only"
        ]):
            return True

    return any(k in q for k in [
        "explain", "what is", "what does", "how does", "tell me about", "details of",
        "describe", "alone", "understand", "overview of", "walk me through", "guide on", "meaning of",
        "hybrid mode", "execution mode", "downtime are not", "is downtime", "why do we", "do we need downtime",
        "why downtime", "difference between", "how it works", "what is lockout",
        "what is user lock", "what is user lockout", "why user lock", "why lockout", "meaning of lockout",
        "why no downtime", "only user lock",
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


def route_after_draft(state: AgentState) -> Literal["consensus_validation", "generate_response"]:
    """Module 3: Route high-risk restricted operations through consensus validation."""
    draft = state.get("draft")
    if draft and draft.get("restricted_operation", False):
        return "consensus_validation"
    return "generate_response"


def build_ticket_agent_graph():
    builder = StateGraph(AgentState)

    # Register Nodes (5 original + 3 new)
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("extract_info", extract_info_node)
    builder.add_node("retrieve_context", retrieve_context_node)       # Module 1: RAG
    builder.add_node("check_completeness", check_completeness_node)
    builder.add_node("generate_draft", generate_draft_node)
    builder.add_node("consensus_validation", consensus_validation_node)  # Module 3: Consensus
    builder.add_node("generate_response", generate_response_node)
    builder.add_node("rai_guard", rai_guard_node)                     # Module 6: RAI

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

    # extract_info → retrieve_context → check_completeness (Module 1 inserted)
    builder.add_edge("extract_info", "retrieve_context")
    builder.add_edge("retrieve_context", "check_completeness")

    builder.add_conditional_edges(
        "check_completeness",
        route_completeness,
        {
            "generate_draft": "generate_draft",
            "generate_response": "generate_response",
        },
    )

    # generate_draft → consensus_validation (restricted) or generate_response (standard)
    builder.add_conditional_edges(
        "generate_draft",
        route_after_draft,
        {
            "consensus_validation": "consensus_validation",
            "generate_response": "generate_response",
        },
    )

    builder.add_edge("consensus_validation", "generate_response")

    # generate_response → rai_guard → END (Module 6 gate)
    builder.add_edge("generate_response", "rai_guard")
    builder.add_edge("rai_guard", END)

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
        "retrieval_context": None,          # Module 1: RAG
        "draft": None,
        "draft_id": current_state.get("draft_id"),
        "draft_status": current_state.get("draft_status"),
        "consensus_result": None,           # Module 3: Consensus
        "needs_human_approval": False,
        "ticket_created": current_state.get("ticket_created"),
        "response_text": None,
        "error": None,
        "rai_flags": None,                  # Module 6: RAI
    }

    result = await ticket_agent_graph.ainvoke(state_input)
    return result
