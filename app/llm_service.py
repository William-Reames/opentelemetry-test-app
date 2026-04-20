"""
LLM service for interacting with Ollama.

This module provides functions for making LLM calls to Ollama with proper
error handling and tracing integration.
"""

import logging
import time
from collections.abc import Mapping
from typing import Any, Dict, Optional

import ollama
from opentelemetry import trace
from traceloop.sdk.decorators import task, workflow

from app.config import Config
from app.langfuse_integration import trace_llm_call

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class OllamaServiceError(Exception):
    """Raised when an Ollama service operation fails."""


def _extract_model_names(models_response: Any) -> list[str]:
    """Normalize Ollama list responses into a list of model names."""
    if isinstance(models_response, Mapping):
        response_models = models_response.get("models", [])
    else:
        response_models = getattr(models_response, "models", [])

    model_names = []
    for listed_model in response_models:
        if isinstance(listed_model, Mapping):
            model_name = listed_model.get("model") or listed_model.get("name", "")
        else:
            model_name = getattr(listed_model, "model", "") or getattr(listed_model, "name", "")

        if model_name:
            model_names.append(model_name)

    return model_names


def _normalize_generate_response(response: Any) -> Mapping[str, Any]:
    """Return a mapping for typed or dict-like Ollama generate responses."""
    if isinstance(response, Mapping):
        return response

    if hasattr(response, "model_dump"):
        return response.model_dump()

    return {
        "response": getattr(response, "response", ""),
        "prompt_eval_count": getattr(response, "prompt_eval_count", 0),
        "eval_count": getattr(response, "eval_count", 0),
    }


def _model_is_available(requested_model: str, available_model: str) -> bool:
    """Match model names with or without tags."""
    available_base = available_model.split(":")[0]
    requested_base = requested_model.split(":")[0]
    return requested_model in (available_model, available_base) or requested_base == available_base


@task(name="check_ollama_connection")
def check_ollama_connection() -> Dict[str, Any]:
    """
    Check if Ollama is running and accessible.

    Returns:
        Dict with status information:
        - available (bool): Whether Ollama is accessible
        - error (str, optional): Error message if not available
        - models (list, optional): List of available models

    Example:
        >>> result = check_ollama_connection()
        >>> if result['available']:
        ...     print(f"Ollama is running with models: {result['models']}")
    """
    try:
        client = ollama.Client(host=Config.OLLAMA_HOST)
        models = _extract_model_names(client.list())

        logger.info("Ollama connection successful. Available models: %s", models)
        return {
            "available": True,
            "models": models,
            "host": Config.OLLAMA_HOST,
        }

    except ollama.ResponseError as exc:
        error_msg = f"Failed to connect to Ollama at {Config.OLLAMA_HOST}: {exc}"
        logger.error("%s", error_msg)
        return {
            "available": False,
            "error": error_msg,
            "host": Config.OLLAMA_HOST,
        }
    except Exception as exc:  # pylint: disable=broad-exception-caught  # pragma: no cover - defensive for transport/runtime issues
        error_msg = f"Failed to connect to Ollama at {Config.OLLAMA_HOST}: {exc}"
        logger.exception("%s", error_msg)
        return {
            "available": False,
            "error": error_msg,
            "host": Config.OLLAMA_HOST,
        }


@task(name="generate_completion")
# pylint: disable=too-many-locals
def generate_completion(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    stream: bool = False,
) -> Dict[str, Any]:
    """
    Generate a completion from Ollama.

    Args:
        prompt: The input prompt for the LLM.
        model: Model name to use (defaults to Config.OLLAMA_MODEL).
        max_tokens: Maximum tokens to generate (optional).
        temperature: Sampling temperature (0.0 to 1.0).
        stream: Whether to stream the response.

    Returns:
        Dict containing:
        - completion (str): The generated text
        - model (str): Model used
        - tokens (int): Total tokens used
        - prompt_tokens (int): Tokens in the prompt
        - completion_tokens (int): Tokens in the completion
        - latency_ms (int): Time taken in milliseconds
        - error (str, optional): Error message if failed

    Raises:
        OllamaServiceError: If Ollama is not available or request fails.

    Example:
        >>> result = generate_completion("What is OpenTelemetry?")
        >>> print(result['completion'])
    """
    selected_model = model or Config.OLLAMA_MODEL
    start_time = time.time()

    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("llm.model", selected_model)
        current_span.set_attribute("llm.prompt_length", len(prompt))
        current_span.set_attribute("llm.temperature", temperature)
        current_span.set_attribute("llm.stream", stream)
        if max_tokens:
            current_span.set_attribute("llm.max_tokens", max_tokens)

    try:
        client = ollama.Client(host=Config.OLLAMA_HOST)
        options = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens

        logger.info(
            "Generating completion with model '%s' for prompt length %s",
            selected_model,
            len(prompt),
        )

        response = _normalize_generate_response(
            client.generate(
                model=selected_model,
                prompt=prompt,
                options=options,
                stream=stream,
            )
        )

        latency_ms = int((time.time() - start_time) * 1000)
        completion = response.get("response", "") or ""
        prompt_tokens = response.get("prompt_eval_count", 0) or 0
        completion_tokens = response.get("eval_count", 0) or 0
        total_tokens = prompt_tokens + completion_tokens

        if current_span and current_span.is_recording():
            current_span.set_attribute("llm.completion_length", len(completion))
            current_span.set_attribute("llm.total_tokens", total_tokens)
            current_span.set_attribute("llm.prompt_tokens", prompt_tokens)
            current_span.set_attribute("llm.completion_tokens", completion_tokens)
            current_span.set_attribute("llm.latency_ms", latency_ms)

        logger.info(
            "Completion generated successfully: %s tokens, %sms latency",
            total_tokens,
            latency_ms,
        )
        
        # Trace to Langfuse
        trace_llm_call(
            prompt=prompt,
            completion=completion,
            model=selected_model,
            tokens=total_tokens,
            latency_ms=latency_ms
        )
        
        return {
            "completion": completion,
            "model": selected_model,
            "tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": latency_ms,
        }

    except ollama.ResponseError as exc:
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Failed to generate completion: {exc}"
        logger.error("%s", error_msg)

        if current_span and current_span.is_recording():
            current_span.set_attribute("error", True)
            current_span.set_attribute("error.message", error_msg)
            current_span.set_attribute("llm.latency_ms", latency_ms)

        raise OllamaServiceError(error_msg) from exc
    except Exception as exc:  # pragma: no cover - defensive for transport/runtime issues
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Failed to generate completion: {exc}"
        logger.exception("%s", error_msg)

        if current_span and current_span.is_recording():
            current_span.set_attribute("error", True)
            current_span.set_attribute("error.message", error_msg)
            current_span.set_attribute("llm.latency_ms", latency_ms)

        raise OllamaServiceError(error_msg) from exc


@workflow(name="llm_complete_workflow")
def complete_with_ollama(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    High-level workflow for LLM completion with connection checking.

    This function wraps the completion process with connection checking
    and is decorated as a Traceloop workflow for better trace organization.

    Args:
        prompt: The input prompt for the LLM.
        model: Model name to use (defaults to Config.OLLAMA_MODEL).
        max_tokens: Maximum tokens to generate (optional).
        temperature: Sampling temperature (0.0 to 1.0).

    Returns:
        Dict containing completion results or error information.

    Example:
        >>> result = complete_with_ollama("Explain tracing")
        >>> if 'error' not in result:
        ...     print(result['completion'])
    """
    connection_status = check_ollama_connection()

    if not connection_status["available"]:
        return {
            "error": "Ollama not available",
            "message": connection_status["error"],
            "suggestion": "Please ensure Ollama is running: ollama serve",
        }

    selected_model = model or Config.OLLAMA_MODEL
    available_models = connection_status.get("models", [])

    if available_models and not any(
        _model_is_available(selected_model, available_model)
        for available_model in available_models
    ):
        return {
            "error": "Model not available",
            "message": f"Model '{selected_model}' is not available",
            "available_models": available_models,
            "suggestion": f"Pull the model first: ollama pull {selected_model}",
        }

    try:
        return generate_completion(
            prompt=prompt,
            model=selected_model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except OllamaServiceError as exc:
        return {
            "error": "Completion failed",
            "message": str(exc),
        }


# Made with Bob
