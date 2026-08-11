"""
Structured output from LLM — the single place in the codebase that makes
classification LLM calls. Both approaches accept a system_prompt argument
so the caller (graph node or retry wrapper) controls prompt content without
touching LLM wiring.

# PRODUCTION NOTE: In a real system, prefer function-calling (approach 1) as
# it is more reliable and model-native. Fall back to JSON mode only for models
# that don't support tool/function calling. Always validate the output with
# Pydantic regardless of which approach you use.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError
from schema import TicketClassification

load_dotenv()

# Change default fallback to your local model
_DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2.3b")

DEFAULT_SYSTEM_PROMPT = "You are an expert customer support ticket classifier."

# Used by fallback_retry on retry attempts — simpler, more conservative
SIMPLE_SYSTEM_PROMPT = (
    "You are a support ticket classifier. Classify into one of: "
    "order_issue, payment_issue, delivery_issue, product_issue, account_issue, refund_request, other. "
    "Keep confidence low and set requires_human_review=True if unsure."
)


# ---------------------------------------------------------------------------
# Approach 1: Function-calling (recommended)
# Use when: the model supports tool/function calling (llama3.2 supports this well)
# Pros: Model is explicitly told the schema; more reliable JSON adherence.
# Cons: Slightly higher token overhead for the schema definition.
# ---------------------------------------------------------------------------

def classify_with_function_calling(
    ticket_text: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    model: str = _DEFAULT_MODEL,
) -> TicketClassification:
    # Instantiate the local Ollama model
    llm = ChatOllama(model=model, temperature=0)
    structured_llm = llm.with_structured_output(TicketClassification)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Classify this support ticket:\n\n{ticket_text}"),
    ])

    chain = prompt | structured_llm
    return chain.invoke({"ticket_text": ticket_text})


# ---------------------------------------------------------------------------
# Approach 2: JSON mode
# Use when: you need the model to freely structure its output as JSON but
# don't want to pin to a specific schema via tool calling.
# Pros: Simpler setup; works across more models.
# Cons: Must parse + validate manually; model may deviate from expected fields.
# ---------------------------------------------------------------------------

def classify_with_json_mode(
    ticket_text: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    model: str = _DEFAULT_MODEL,
) -> TicketClassification:
    schema_json = json.dumps(TicketClassification.model_json_schema(), indent=2)
    # Escape braces so LangChain's template engine doesn't treat them as
    # variable placeholders (e.g. {"type": "string"} → {{"type": "string"}})
    schema_escaped = schema_json.replace("{", "{{").replace("}", "}}")
    full_system = f"{system_prompt}\n\nReturn ONLY valid JSON matching this schema:\n{schema_escaped}"

    # Ollama uses format="json" instead of response_format dicts
    llm = ChatOllama(
        model=model,
        temperature=0,
        format="json"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", full_system),
        ("human", "Classify this support ticket:\n\n{ticket_text}"),
    ])

    chain = prompt | llm
    response = chain.invoke({"ticket_text": ticket_text})
    
    raw = json.loads(response.content)
    print(json.dumps(raw, indent=4))
    return TicketClassification.model_validate(raw)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ticket = "I was charged twice for order #9981. Please refund immediately!"

    print("=== Approach 1: Function-calling ===")
    result1 = classify_with_function_calling(ticket)
    print(result1.model_dump_json(indent=2))

    print("\n=== Approach 2: JSON mode ===")
    result2 = classify_with_json_mode(ticket)
    print(result2.model_dump_json(indent=2))