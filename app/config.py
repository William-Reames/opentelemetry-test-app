"""
Configuration management for the AI Tracing Prototype.

Loads configuration from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config:  # pylint: disable=too-few-public-methods
    """Application configuration class."""

    # Flask Configuration
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    PORT = int(os.getenv("PORT", "5000"))

    # Ollama Configuration
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))

    # ChromaDB Configuration
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "documents")

    # Tracing Backend Configuration
    # Options: traceloop, langfuse, traceloop,langfuse, none
    TRACING_BACKEND = os.getenv("TRACING_BACKEND", "traceloop")

    # OpenLLMetry / Traceloop Configuration
    TRACELOOP_API_KEY = os.getenv("TRACELOOP_API_KEY")
    TRACELOOP_DISABLE_BATCH = os.getenv("TRACELOOP_DISABLE_BATCH", "false").lower() == "true"

    # LangFuse Configuration
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

    # OpenTelemetry Configuration
    OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "ai-tracing-prototype")
    OTEL_LOG_LEVEL = os.getenv("OTEL_LOG_LEVEL", "info")
@classmethod
def validate(cls):
    """
    Validate required configuration values.

    Raises:
        ValueError: If required configuration is missing.
    """
    # pylint: disable=no-member
    backends = [b.strip() for b in cls.TRACING_BACKEND.split(',')]

    # Validate TraceLoop configuration if enabled
    if 'traceloop' in backends:
        if not cls.TRACELOOP_API_KEY:
            print("WARNING: TRACELOOP_API_KEY not set but traceloop backend is enabled.")
            print("Get your API key from https://app.traceloop.com")

    # Validate LangFuse configuration if enabled
    if 'langfuse' in backends:
        if not cls.LANGFUSE_PUBLIC_KEY or not cls.LANGFUSE_SECRET_KEY:
            print("WARNING: LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not set "
                  "but langfuse backend is enabled.")
            print("Configure LangFuse keys from your LangFuse instance.")

    @classmethod
    def display(cls):
        """Display current configuration (excluding sensitive values)."""
        print("\n=== Application Configuration ===")
        print(f"Flask Environment: {cls.FLASK_ENV}")
        print(f"Flask Debug: {cls.FLASK_DEBUG}")
        print(f"Port: {cls.PORT}")
        print(f"Ollama Host: {cls.OLLAMA_HOST}")
        print(f"Ollama Model: {cls.OLLAMA_MODEL}")
        print(f"Ollama Timeout: {cls.OLLAMA_TIMEOUT}s")
        print(f"ChromaDB Persist Dir: {cls.CHROMA_PERSIST_DIR}")
        print(f"ChromaDB Collection: {cls.CHROMA_COLLECTION}")
        print(f"Tracing Backend: {cls.TRACING_BACKEND}")
        print(f"Traceloop API Key: {'Set' if cls.TRACELOOP_API_KEY else 'Not Set'}")
        print(f"LangFuse Public Key: {'Set' if cls.LANGFUSE_PUBLIC_KEY else 'Not Set'}")
        print(f"LangFuse Host: {cls.LANGFUSE_HOST}")
        print(f"OpenTelemetry Service Name: {cls.OTEL_SERVICE_NAME}")
        print("================================\n")

# Made with Bob
