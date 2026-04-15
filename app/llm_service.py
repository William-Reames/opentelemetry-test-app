"""
LLM service for interacting with Ollama.

This module provides functions for making LLM calls to Ollama with proper
error handling and tracing integration.
"""

import time
import logging
from typing import Dict, Any, Optional

import ollama
from opentelemetry import trace
from traceloop.sdk.decorators import workflow, task

from app.config import Config

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


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
        # Try to list available models as a connection check
        client = ollama.Client(host=Config.OLLAMA_HOST)
        models_response = client.list()
        
        # Extract model names from the response
        models = []
        if hasattr(models_response, 'models'):
            models = [model.model for model in models_response.models]
        elif isinstance(models_response, dict) and 'models' in models_response:
            models = [model.get('name', model.get('model', '')) 
                     for model in models_response['models']]
        
        logger.info(f"Ollama connection successful. Available models: {models}")
        
        return {
            'available': True,
            'models': models,
            'host': Config.OLLAMA_HOST
        }
    
    except Exception as e:
        error_msg = f"Failed to connect to Ollama at {Config.OLLAMA_HOST}: {str(e)}"
        logger.error(error_msg)
        
        return {
            'available': False,
            'error': error_msg,
            'host': Config.OLLAMA_HOST
        }


@task(name="generate_completion")
def generate_completion(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    stream: bool = False
) -> Dict[str, Any]:
    """
    Generate a completion from Ollama.
    
    Args:
        prompt: The input prompt for the LLM.
        model: Model name to use (defaults to Config.OLLAMA_MODEL).
        max_tokens: Maximum tokens to generate (optional).
        temperature: Sampling temperature (0.0 to 1.0).
        stream: Whether to stream the response (not implemented in this version).
    
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
        Exception: If Ollama is not available or request fails.
    
    Example:
        >>> result = generate_completion("What is OpenTelemetry?")
        >>> print(result['completion'])
    """
    model = model or Config.OLLAMA_MODEL
    start_time = time.time()
    
    # Add span attributes for the LLM call
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("llm.model", model)
        current_span.set_attribute("llm.prompt_length", len(prompt))
        current_span.set_attribute("llm.temperature", temperature)
        if max_tokens:
            current_span.set_attribute("llm.max_tokens", max_tokens)
    
    try:
        client = ollama.Client(host=Config.OLLAMA_HOST)
        
        # Prepare options
        options = {
            'temperature': temperature,
        }
        if max_tokens:
            options['num_predict'] = max_tokens
        
        logger.info(f"Generating completion with model '{model}' for prompt length {len(prompt)}")
        
        # Make the API call
        response = client.generate(
            model=model,
            prompt=prompt,
            options=options,
            stream=False
        )
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Extract response data
        completion = response.get('response', '')
        
        # Token counting (Ollama provides these in the response)
        prompt_tokens = response.get('prompt_eval_count', 0)
        completion_tokens = response.get('eval_count', 0)
        total_tokens = prompt_tokens + completion_tokens
        
        # Add completion attributes to span
        if current_span and current_span.is_recording():
            current_span.set_attribute("llm.completion_length", len(completion))
            current_span.set_attribute("llm.total_tokens", total_tokens)
            current_span.set_attribute("llm.prompt_tokens", prompt_tokens)
            current_span.set_attribute("llm.completion_tokens", completion_tokens)
            current_span.set_attribute("llm.latency_ms", latency_ms)
        
        logger.info(
            f"Completion generated successfully: {total_tokens} tokens, "
            f"{latency_ms}ms latency"
        )
        
        return {
            'completion': completion,
            'model': model,
            'tokens': total_tokens,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'latency_ms': latency_ms
        }
    
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Failed to generate completion: {str(e)}"
        logger.error(error_msg)
        
        # Add error to span
        if current_span and current_span.is_recording():
            current_span.set_attribute("error", True)
            current_span.set_attribute("error.message", error_msg)
            current_span.set_attribute("llm.latency_ms", latency_ms)
        
        raise Exception(error_msg)


@workflow(name="llm_complete_workflow")
def complete_with_ollama(
    prompt: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7
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
    # First check if Ollama is available
    connection_status = check_ollama_connection()
    
    if not connection_status['available']:
        return {
            'error': 'Ollama not available',
            'message': connection_status['error'],
            'suggestion': 'Please ensure Ollama is running: ollama serve'
        }
    
    # Check if the requested model is available
    model = model or Config.OLLAMA_MODEL
    available_models = connection_status.get('models', [])
    
    if available_models and model not in available_models:
        return {
            'error': 'Model not available',
            'message': f"Model '{model}' is not available",
            'available_models': available_models,
            'suggestion': f"Pull the model first: ollama pull {model}"
        }
    
    # Generate the completion
    try:
        result = generate_completion(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return result
    
    except Exception as e:
        return {
            'error': 'Completion failed',
            'message': str(e)
        }

# Made with Bob