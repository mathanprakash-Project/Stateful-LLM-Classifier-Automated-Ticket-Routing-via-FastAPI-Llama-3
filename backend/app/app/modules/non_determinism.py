"""
Controlling non-determinism in LLM outputs via temperature.
"""

import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from app.schema import TicketClassification

load_dotenv()

_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://localhost:11434"))


def build_deterministic_llm(model: str = "llama3.2:3b") -> ChatOllama:
    """
    temperature=0  → greedy decoding, most probable token always chosen.
    """
    return ChatOllama(
        model=model,
        temperature=0,
        base_url=_OLLAMA_BASE_URL,
    )


def build_creative_llm(model: str = "llama3.2:3b", temperature: float = 0.7) -> ChatOllama:
    """
    Higher temperature for tasks where variation is desirable.
    """
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url=_OLLAMA_BASE_URL,
    )


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
    """
    llm = build_deterministic_llm()
    results = [classify_ticket(ticket_text, llm) for _ in range(runs)]
    categories = [r.issue_category for r in results]
    all_match = len(set(categories)) == 1
    
    return {
        "all_match": all_match,
        "category": categories[0] if all_match else "MISMATCH",
        "all_categories": [c.value for c in categories],
    }


if __name__ == "__main__":
    ticket = "My package was supposed to arrive 5 days ago. Where is it?"

    print("Running consistency test (5 runs, temperature=0)...")
    summary = run_consistency_test(ticket)
    print(f"All outputs match: {summary['all_match']}")
    print(f"Category        : {summary['category']}")
    print(f"All categories  : {summary['all_categories']}")

    assert summary["all_match"], "Determinism test failed — outputs are not consistent!"
    print("\nDeterminism test PASSED.")
