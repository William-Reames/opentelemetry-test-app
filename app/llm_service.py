"""
LLM service for interacting with Ollama via LangChain.

This module provides functions for making LLM calls to Ollama using LangChain's
ChatOllama with proper error handling and tracing integration.
"""

import logging
import time
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from opentelemetry import trace
from traceloop.sdk.decorators import task

from app.config import Config
from app.langfuse_integration import trace_llm_call

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class OllamaServiceError(Exception):
    """Raised when an Ollama service operation fails."""


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
    Generate a completion from Ollama using LangChain's ChatOllama.

    Args:
        prompt: The input prompt for the LLM.
        model: Model name to use (defaults to Config.OLLAMA_MODEL).
        max_tokens: Maximum tokens to generate (optional).
        temperature: Sampling temperature (0.0 to 1.0).
        stream: Whether to stream the response (not currently used).

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
        # Create ChatOllama instance with configuration
        llm_kwargs = {
            "base_url": Config.OLLAMA_HOST,
            "model": selected_model,
            "temperature": temperature,
        }
        if max_tokens:
            llm_kwargs["num_predict"] = max_tokens

        llm = ChatOllama(**llm_kwargs)

        logger.info(
            "Generating completion with model '%s' for prompt length %s",
            selected_model,
            len(prompt),
        )

        # Invoke the LLM with a HumanMessage
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract completion text from AIMessage
        completion = response.content

        # Extract token counts from response metadata
        metadata = getattr(response, 'response_metadata', {})
        prompt_tokens = metadata.get("prompt_eval_count", 0) or 0
        completion_tokens = metadata.get("eval_count", 0) or 0
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

    except Exception as exc:  # pragma: no cover - defensive for transport/runtime issues
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Failed to generate completion: {exc}"
        logger.exception("%s", error_msg)

        if current_span and current_span.is_recording():
            current_span.set_attribute("error", True)
            current_span.set_attribute("error.message", error_msg)
            current_span.set_attribute("llm.latency_ms", latency_ms)

        raise OllamaServiceError(error_msg) from exc


# Made with Bob
