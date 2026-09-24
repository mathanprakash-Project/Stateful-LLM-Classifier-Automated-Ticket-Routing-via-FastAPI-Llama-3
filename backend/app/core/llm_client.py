"""
Centralized LLM client for Ollama with automatic model fallback and timeout management.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


async def call_ollama(
    prompt: str,
    format_json: bool = False,
    system_prompt: Optional[str] = None,
    preferred_model: Optional[str] = None,
    task_tier: Optional[str] = None,
) -> Optional[str]:
    """
    Calls Ollama API with fallback across candidate models (e.g. configured model -> local llama3.2:3b).

    Args:
        task_tier: Model routing tier — "micro", "mid", or "strong".
                   Maps to settings.MODEL_TIER_MICRO/MID/STRONG for cost-optimized routing.
                   If None, uses DEFAULT_MODEL (backward compatible).
    """
    if settings.LLM_PROVIDER == "mock":
        return None

    # Model Routing: select the right model based on pipeline stage
    tier_model = None
    if task_tier:
        tier_map = {
            "micro": settings.MODEL_TIER_MICRO,
            "mid": settings.MODEL_TIER_MID,
            "strong": settings.MODEL_TIER_STRONG,
        }
        tier_model = tier_map.get(task_tier.lower())

    # Candidate models to try in order
    candidate_models: List[str] = []
    if tier_model:
        candidate_models.append(tier_model)
    if preferred_model and preferred_model not in candidate_models:
        candidate_models.append(preferred_model)
    if settings.DEFAULT_MODEL and settings.DEFAULT_MODEL not in candidate_models:
        candidate_models.append(settings.DEFAULT_MODEL)
    
    # Common local models
    for local_fallback in ["llama3.2:3b", "llama3.2", "llama3"]:
        if local_fallback not in candidate_models:
            candidate_models.append(local_fallback)

    payload: Dict[str, Any] = {
        "prompt": prompt,
        "stream": False,
    }
    if format_json:
        payload["format"] = "json"
    if system_prompt:
        payload["system"] = system_prompt

    import time
    from app.core.model_tracker import model_tracker
    start_time = time.time()

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
        for model_name in candidate_models:
            payload["model"] = model_name
            try:
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data.get("response", "").strip()
                    if response_text:
                        duration_ms = (time.time() - start_time) * 1000
                        p_tokens = data.get("prompt_eval_count") or max(int(len(prompt.split()) * 1.3), 10)
                        c_tokens = data.get("eval_count") or max(int(len(response_text.split()) * 1.3), 5)
                        model_tracker.record_llm_call(
                            model=model_name,
                            tier=task_tier,
                            prompt_tokens=p_tokens,
                            completion_tokens=c_tokens,
                            latency_ms=duration_ms,
                            status="success",
                        )
                        return response_text
                elif resp.status_code in (401, 403, 404):
                    logger.info("Model '%s' returned HTTP %s on Ollama, trying next candidate...", model_name, resp.status_code)
                    continue
                else:
                    logger.warning("Ollama call for model '%s' failed with HTTP %s: %s", model_name, resp.status_code, resp.text[:200])
            except httpx.ConnectError:
                logger.warning("Could not connect to Ollama at %s", settings.OLLAMA_BASE_URL)
                break
            except httpx.TimeoutException:
                logger.warning("Ollama query timed out for model %s after %ss", model_name, settings.LLM_TIMEOUT)
                continue
            except Exception as exc:
                logger.warning("Error querying Ollama with model %s: %s", model_name, exc)
                continue

    return None

