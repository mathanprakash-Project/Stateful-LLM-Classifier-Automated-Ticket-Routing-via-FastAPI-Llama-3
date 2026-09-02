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
) -> Optional[str]:
    """
    Calls Ollama API with fallback across candidate models (e.g. configured model -> local llama3.2:3b).
    """
    if settings.LLM_PROVIDER == "mock":
        return None

    # Candidate models to try in order
    candidate_models: List[str] = []
    if preferred_model:
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

