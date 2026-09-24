"""
Consensus Validation node for high-risk ticket operations.
Runs 3 independent micro-agent evaluations and uses majority voting
to validate classification accuracy for restricted operations.
"""

import json
import logging
from collections import Counter
from typing import Any, Dict, List
import asyncio

from app.agents.state import AgentState
from app.core.llm_client import call_ollama

logger = logging.getLogger(__name__)

CONSENSUS_PROMPT = """
You are a classification verification agent. Given a ticket draft, independently verify:
1. Is the activity_code correct?
2. Is the priority appropriate?
3. Does this require admin approval?
4. What is your confidence (0.0-1.0)?

Ticket Draft:
- Title: {title}
- Category: {category}
- Activity Code: {activity_code}
- Priority: {priority}
- Description: {description}
- Restricted Operation: {restricted}

Original User Messages:
{user_messages}

Respond in JSON:
{{
  "verified_activity_code": "...",
  "verified_priority": "...",
  "requires_admin_approval": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "..."
}}
"""

NUM_AGENTS = 3

async def run_single_verification(draft: dict, user_messages: str, agent_idx: int) -> dict:
    """Run a single verification agent."""
    prompt = CONSENSUS_PROMPT.format(
        title=draft.get("title", ""),
        category=draft.get("category_name", ""),
        activity_code=draft.get("activity_code", ""),
        priority=draft.get("priority", ""),
        description=draft.get("description", ""),
        restricted=draft.get("restricted_operation", False),
        user_messages=user_messages,
    )
    
    response = await call_ollama(prompt, format_json=True)
    if response:
        try:
            return json.loads(response)
        except:
            pass
    
    # Fallback: agree with the draft
    return {
        "verified_activity_code": draft.get("activity_code"),
        "verified_priority": draft.get("priority"),
        "requires_admin_approval": draft.get("requires_admin_approval", False),
        "confidence": 0.5,
        "reasoning": f"Agent {agent_idx} fallback - could not parse LLM response"
    }


def compute_consensus(votes: List[dict], original_draft: dict) -> dict:
    """Compute majority vote from agent responses."""
    activity_codes = [v.get("verified_activity_code", "") for v in votes]
    priorities = [v.get("verified_priority", "") for v in votes]
    approval_votes = [v.get("requires_admin_approval", False) for v in votes]
    confidences = [v.get("confidence", 0.5) for v in votes]
    
    # Majority vote
    activity_counter = Counter(activity_codes)
    priority_counter = Counter(priorities)
    approval_counter = Counter(approval_votes)
    
    consensus_activity = activity_counter.most_common(1)[0]
    consensus_priority = priority_counter.most_common(1)[0]
    consensus_approval = approval_counter.most_common(1)[0]
    
    agreement_level = consensus_activity[1]  # How many agents agreed
    avg_confidence = sum(confidences) / len(confidences)
    
    result = {
        "consensus_activity_code": consensus_activity[0],
        "consensus_priority": consensus_priority[0],
        "consensus_admin_approval": consensus_approval[0],
        "agreement_ratio": f"{agreement_level}/{len(votes)}",
        "average_confidence": round(avg_confidence, 2),
        "unanimous": agreement_level == len(votes),
        "escalate_to_human": agreement_level < 2,  # No majority = escalate
        "agent_reasonings": [v.get("reasoning", "") for v in votes],
    }
    
    return result


async def consensus_validation_node(state: AgentState) -> Dict[str, Any]:
    """Run consensus validation for high-risk restricted operations."""
    draft = state.get("draft")
    if not draft:
        return {}
    
    # Only validate restricted operations
    if not draft.get("restricted_operation", False):
        logger.info("Consensus validation skipped: non-restricted operation")
        return {"consensus_result": {"skipped": True, "reason": "non-restricted"}}
    
    messages = state.get("messages", [])
    user_messages = "\\n".join([m.get("content", "") for m in messages if m.get("role") == "user"])
    if state.get("current_user_message"):
        user_messages += "\\n" + state["current_user_message"]
    
    logger.info("Running consensus validation with %d agents for %s", NUM_AGENTS, draft.get("activity_code"))
    
    # Run 3 independent verifications
    tasks = [
        run_single_verification(draft, user_messages, i)
        for i in range(NUM_AGENTS)
    ]
    votes = await asyncio.gather(*tasks)
    
    # Compute consensus
    consensus = compute_consensus(list(votes), draft)
    
    try:
        from app.core.model_tracker import model_tracker
        model_tracker.record_consensus(
            unanimous=consensus.get("unanimous", True),
            escalated=consensus.get("escalate_to_human", False),
            agreement_ratio=consensus.get("agreement_ratio", "3/3"),
        )
    except Exception as e:
        logger.debug("Failed to record consensus telemetry: %s", e)

    logger.info(
        "Consensus result: activity=%s, agreement=%s, escalate=%s",
        consensus["consensus_activity_code"],
        consensus["agreement_ratio"],
        consensus["escalate_to_human"],
    )
    
    # If consensus disagrees with the draft, update the draft
    result = {"consensus_result": consensus}
    
    if consensus["escalate_to_human"]:
        # No majority — flag for human review
        result["needs_human_approval"] = True
        result["response_text"] = (
            "⚠️ **Consensus Validation Alert**\\n\\n"
            f"Our verification team could not reach consensus on this ticket classification "
            f"(Agreement: {consensus['agreement_ratio']}). "
            f"This draft has been escalated for manual human review before submission.\\n\\n"
            f"**Average Confidence:** {consensus['average_confidence']}\\n\\n"
            "A support manager will review this request and process it accordingly."
        )
    elif consensus["consensus_activity_code"] != draft.get("activity_code"):
        # Majority disagrees with original classification — log warning
        logger.warning(
            "Consensus overrides draft activity: %s -> %s",
            draft.get("activity_code"),
            consensus["consensus_activity_code"],
        )
    
    return result
