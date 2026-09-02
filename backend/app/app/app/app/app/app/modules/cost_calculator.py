"""
Token count approximation and session-level cost tracking for local models.

# PRODUCTION NOTE: Local models (like Ollama) incur $0 API cost, but 
# tracking approximate token usage remains valuable for performance 
# monitoring, capacity planning, and latency optimization.
"""

import tiktoken
from dataclasses import dataclass

PRICING: dict[str, dict[str, float]] = {
    "llama3.2:3b": {"input": 0.0, "output": 0.0},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4-turbo": {"input": 0.010, "output": 0.030},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}


@dataclass
class CostInfo:
    model: str
    input_tokens: int
    output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float


class SessionCostTracker:
    """Accumulates cost across multiple LLM calls in a session."""

    def __init__(self):
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0
        self._total_cost_usd: float = 0.0
        self._call_count: int = 0

    def record(self, cost_info: CostInfo) -> None:
        self._total_input_tokens += cost_info.input_tokens
        self._total_output_tokens += cost_info.output_tokens
        self._total_cost_usd += cost_info.total_cost_usd
        self._call_count += 1

    @property
    def summary(self) -> dict:
        return {
            "calls": self._call_count,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_cost_usd": round(self._total_cost_usd, 6),
        }


session_tracker = SessionCostTracker()


def count_tokens(text: str, model: str = "llama3.2:3b") -> int:
    """
    Count approximate tokens in a string using tiktoken.
    For non-OpenAI models like Ollama, this falls back to cl100k_base.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    record_to_session: bool = True,
) -> CostInfo:
    """Calculate cost for an LLM call and optionally record to session tracker."""
    pricing = PRICING.get(model, PRICING["llama3.2:3b"])
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    total = input_cost + output_cost

    info = CostInfo(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_usd=round(input_cost, 6),
        output_cost_usd=round(output_cost, 6),
        total_cost_usd=round(total, 6),
    )

    if record_to_session:
        session_tracker.record(info)

    return info


if __name__ == "__main__":
    prompt = "Classify this ticket: My order hasn't arrived after 2 weeks!"
    response = '{"issue_category": "delivery_issue", "priority": "high"}'

    in_tokens = count_tokens(prompt)
    out_tokens = count_tokens(response)

    cost = calculate_cost("llama3.2:3b", in_tokens, out_tokens)

    print(f"Input tokens : {cost.input_tokens}")
    print(f"Output tokens: {cost.output_tokens}")
    print(f"Input cost   : ${cost.input_cost_usd:.6f}")
    print(f"Output cost  : ${cost.output_cost_usd:.6f}")
    print(f"Total cost   : ${cost.total_cost_usd:.6f}")
    print(f"Session total: {session_tracker.summary}")

