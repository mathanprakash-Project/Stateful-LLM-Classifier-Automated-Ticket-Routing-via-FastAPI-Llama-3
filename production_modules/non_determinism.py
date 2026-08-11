"""
Controlling non-determinism in LLM outputs via temperature.

# PRODUCTION NOTE: Use temperature=0 for classification/routing tasks
# where consistency is critical. Reserve higher temperatures (0.3-0.7) for
# generative tasks like drafting responses or summaries where creative variation
# improves quality.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from schema import TicketClassification

load_dotenv()


def build_deterministic_llm(model: str = "llama3.2.3b") -> ChatOllama:
    """
    temperature=0  → greedy decoding, most probable token always chosen.
    This gives near-identical outputs for the same input.
    """
    return ChatOllama(
        model=model,
        temperature=0,
    )


def build_creative_llm(model: str = "llama3.2.3b", temperature: float = 0.7) -> ChatOllama:
    """
    Higher temperature for tasks where variation is desirable, e.g.
    generating empathetic reply drafts or brainstorming resolutions.
    """
    return ChatOllama(model=model, temperature=temperature)


def classify_ticket(ticket_text: str, llm: ChatOllama) -> TicketClassification:
    structured_llm = llm.with_structured_output(TicketClassification)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert customer support ticket classifier."),
        ("human", "Classify this support ticket:\n\n{ticket_text}"),
    ])
    chain = prompt | structured_llm
    return chain.invoke({"ticket_text": ticket_text})


def run_consistency_test(ticket_text: str, runs: int = 5) -> dict:
    """
    Run the same ticket N times with temperature=0 and assert all categories match.
    Returns a summary dict.
    """
    llm = build_deterministic_llm()
    
    # Run the classification multiple times
    results = [classify_ticket(ticket_text, llm) for _ in range(runs)]
    
    # Extract just the category names from the results
    categories = [r.issue_category for r in results]
    
    # Check if all categories in the list are identical
    all_match = len(set(categories)) == 1
    
    return {
        "all_match": all_match,
        "category": categories[0] if all_match else "MISMATCH",
        "all_categories": [c.value for c in categories],
    }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ticket = "My package was supposed to arrive 5 days ago. Where is it?"

    print("Running consistency test (5 runs, temperature=0)...")
    summary = run_consistency_test(ticket)
    print(f"All outputs match: {summary['all_match']}")
    print(f"Category        : {summary['category']}")
    print(f"All categories  : {summary['all_categories']}")

    assert summary["all_match"], "Determinism test failed — outputs are not consistent!"
    print("\nDeterminism test PASSED.")