"""
Structured output from LLM — the single place in the codebase that makes
classification LLM calls.
"""

import json
import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from app.schema import TicketClassification

load_dotenv()

_DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://localhost:11434"))

DEFAULT_SYSTEM_PROMPT = "You are an expert customer support ticket classifier."

SIMPLE_SYSTEM_PROMPT = (
    "You are a support ticket classifier. Classify into one of: "
    "order_issue, payment_issue, delivery_issue, product_issue, account_issue, refund_request, other. "
    "Keep confidence low and set requires_human_review=True if unsure."
)

JSON_FORMAT_INSTRUCTIONS = """
Return ONLY a valid JSON instance object matching this exact structure:
{
  "issue_category": "order_issue" | "payment_issue" | "delivery_issue" | "product_issue" | "account_issue" | "refund_request" | "other",
  "assigned_team": "fulfillment_team" | "payments_team" | "logistics_team" | "customer_support" | "tech_team",
  "priority": "low" | "medium" | "high" | "critical",
  "user_sentiment": "positive" | "neutral" | "negative" | "angry",
  "confidence_score": 0.95,
  "reasoning": "One line explanation of classification",
  "requires_human_review": false
}

IMPORTANT: Do NOT output JSON schema wrappers like 'properties', '$defs', or 'type'. Output ONLY the key-value pairs of the classification object directly.
"""


def classify_with_function_calling(
    ticket_text: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    model: str = _DEFAULT_MODEL,
) -> TicketClassification:
    llm = ChatOllama(
        model=model,
        temperature=0,
        base_url=_OLLAMA_BASE_URL,
    )
    structured_llm = llm.with_structured_output(TicketClassification)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Classify this support ticket:\n\n{ticket_text}"),
    ])

    chain = prompt | structured_llm
    return chain.invoke({"ticket_text": ticket_text})


def classify_with_json_mode(
    ticket_text: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    model: str = _DEFAULT_MODEL,
) -> TicketClassification:
    full_system = f"{system_prompt}\n\n{JSON_FORMAT_INSTRUCTIONS}"

    llm = ChatOllama(
        model=model,
        temperature=0,
        format="json",
        base_url=_OLLAMA_BASE_URL,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", full_system),
        ("human", "Classify this support ticket:\n\n{ticket_text}"),
    ])

    chain = prompt | llm
    response = chain.invoke({"ticket_text": ticket_text})
    
    raw = json.loads(response.content)
    if isinstance(raw, dict) and "properties" in raw and isinstance(raw["properties"], dict):
        raw = raw["properties"]
        
    print(json.dumps(raw, indent=4))
    return TicketClassification.model_validate(raw)


if __name__ == "__main__":
    ticket = "I was charged twice for order #9981. Please refund immediately!"

    print("=== Approach 1: Function-calling ===")
    result1 = classify_with_function_calling(ticket)
    print(result1.model_dump_json(indent=2))

    print("\n=== Approach 2: JSON mode ===")
    result2 = classify_with_json_mode(ticket)
    print(result2.model_dump_json(indent=2))
