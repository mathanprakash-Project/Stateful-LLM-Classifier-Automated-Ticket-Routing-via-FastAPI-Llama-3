import logging
from typing import Dict, Any

from app.agents.state import AgentState
from app.core.retrieval import get_retriever

logger = logging.getLogger(__name__)

async def retrieve_context_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node to retrieve relevant context from the knowledge base using hybrid search.
    """
    logger.info("Running retrieve_context_node...")
    
    user_message = state.get("current_user_message", "")
    extracted_fields = state.get("extracted_fields", {})
    act_code = state.get("activity_code") or state.get("intent") or ""
    category = extracted_fields.get("category", "")
    title = extracted_fields.get("title", "")
    
    query_parts = []
    if act_code and act_code != "UNKNOWN":
        query_parts.append(act_code.replace("_", " "))
    if category:
        query_parts.append(str(category))
    if title:
        query_parts.append(str(title))
    if user_message:
        query_parts.append(user_message)
        
    query = " ".join(query_parts).strip()
    
    if not query:
        logger.warning("Empty query constructed. Returning empty retrieval context.")
        return {"retrieval_context": []}
        
    logger.debug(f"Executing hybrid search with query: {query}")
    retriever = get_retriever()
    results = retriever.hybrid_search(query, top_k=3)
    
    try:
        from app.core.model_tracker import model_tracker
        model_tracker.record_retrieval(query=query, results_count=len(results), category=str(category))
    except Exception as e:
        logger.debug("Failed to record retrieval telemetry: %s", e)

    return {"retrieval_context": results}

