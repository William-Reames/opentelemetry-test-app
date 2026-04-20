"""Langfuse integration for LLM observability using HTTP API."""

import logging
import requests
import uuid
from datetime import datetime
from app.config import Config

logger = logging.getLogger(__name__)

def configure_langfuse_otlp():
    """Log that Langfuse is configured via HTTP API."""
    if Config.LANGFUSE_PUBLIC_KEY and Config.LANGFUSE_SECRET_KEY:
        logger.info(f"Langfuse HTTP API configured for {Config.LANGFUSE_HOST}")
    else:
        logger.warning("Langfuse keys not configured")

def trace_llm_call(prompt: str, completion: str, model: str,
                   tokens: int, latency_ms: int):
    """
    Trace an LLM call to Langfuse using the HTTP API.
    Creates a generation observation that will appear in Langfuse UI.
    """
    public_key = Config.LANGFUSE_PUBLIC_KEY
    secret_key = Config.LANGFUSE_SECRET_KEY
    host = Config.LANGFUSE_HOST
    
    if not public_key or not secret_key:
        return
    
    try:
        # Generate IDs
        trace_id = str(uuid.uuid4())
        generation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Create trace via HTTP API
        trace_data = {
            "id": trace_id,
            "name": "llm_completion",
            "timestamp": timestamp,
            "metadata": {"source": "ollama"}
        }
        
        # Create generation via HTTP API
        # Note: Use 'prompt' and 'completion' fields for text to be stored in database
        generation_data = {
            "id": generation_id,
            "traceId": trace_id,
            "type": "GENERATION",
            "name": "ollama_generation",
            "startTime": timestamp,
            "endTime": timestamp,
            "model": model,
            "prompt": prompt,
            "completion": completion,
            "usage": {
                "total": tokens
            },
            "metadata": {
                "latency_ms": latency_ms
            }
        }
        
        # Send to Langfuse
        auth = (public_key, secret_key)
        
        # Create trace
        response = requests.post(
            f"{host}/api/public/traces",
            json=trace_data,
            auth=auth,
            timeout=5
        )
        response.raise_for_status()
        
        # Create generation
        response = requests.post(
            f"{host}/api/public/generations",
            json=generation_data,
            auth=auth,
            timeout=5
        )
        response.raise_for_status()
        
        logger.info(f"Traced LLM call to Langfuse: {model}, {tokens} tokens")
    except Exception as exc:
        logger.error(f"Failed to trace to Langfuse: {exc}")

# Made with Bob