"""
Telemetry initialization for the AI Tracing Prototype.

This module configures OpenTelemetry with multi-backend support (TraceLoop and LangFuse).
"""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from traceloop.sdk import Traceloop

# Try to import LangFuse (optional dependency)
try:
    from langfuse.opentelemetry import LangfuseSpanProcessor
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    LangfuseSpanProcessor = None

_TRACING_INITIALIZED = False


def initialize_telemetry(app, config):
    """
    Initialize tracing for the Flask application with multi-backend support.

    Supports TraceLoop, LangFuse, or both backends simultaneously based on
    the TRACING_BACKEND configuration.

    This function is safe to call multiple times; initialization will only
    happen once per process.

    Args:
        app: Flask application instance.
        config: Application configuration object.
    """
    global _TRACING_INITIALIZED

    if _TRACING_INITIALIZED:
        return

    logger = app.logger or logging.getLogger(__name__)
    
    # Parse backend configuration
    backends = [b.strip().lower() for b in config.TRACING_BACKEND.split(',')]
    
    if 'none' in backends:
        logger.info("Tracing disabled (TRACING_BACKEND=none)")
        _TRACING_INITIALIZED = True
        return
    
    logger.info("Initializing tracing with backends: %s", ', '.join(backends))
    
    # Initialize TraceLoop if enabled
    if 'traceloop' in backends:
        if Traceloop is None:
            logger.warning("Traceloop SDK is not installed; skipping Traceloop backend.")
        elif not config.TRACELOOP_API_KEY:
            logger.warning("TRACELOOP_API_KEY is not set; skipping Traceloop backend.")
        else:
            try:
                Traceloop.init(
                    app_name=config.OTEL_SERVICE_NAME,
                    api_key=config.TRACELOOP_API_KEY,
                    disable_batch=config.TRACELOOP_DISABLE_BATCH,
                )
                logger.info("✓ Traceloop backend initialized for service '%s'", config.OTEL_SERVICE_NAME)
            except Exception as exc:  # pragma: no cover - defensive path
                logger.warning("Traceloop initialization failed: %s", exc)
    
    # Initialize LangFuse if enabled
    if 'langfuse' in backends:
        if not LANGFUSE_AVAILABLE:
            logger.warning("LangFuse SDK is not installed; skipping LangFuse backend.")
            logger.warning("Install with: uv add langfuse")
        elif not config.LANGFUSE_PUBLIC_KEY or not config.LANGFUSE_SECRET_KEY:
            logger.warning("LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not set; skipping LangFuse backend.")
        else:
            try:
                tracer_provider = trace.get_tracer_provider()
                langfuse_processor = LangfuseSpanProcessor(
                    public_key=config.LANGFUSE_PUBLIC_KEY,
                    secret_key=config.LANGFUSE_SECRET_KEY,
                    host=config.LANGFUSE_HOST,
                )
                tracer_provider.add_span_processor(langfuse_processor)
                logger.info("✓ LangFuse backend initialized (host: %s)", config.LANGFUSE_HOST)
            except Exception as exc:  # pragma: no cover - defensive path
                logger.warning("LangFuse initialization failed: %s", exc)

    # Instrument Flask (works with all backends)
    try:
        FlaskInstrumentor().instrument_app(app)
        _TRACING_INITIALIZED = True
        logger.info("✓ Flask OpenTelemetry instrumentation enabled")
    except Exception as exc:  # pragma: no cover - defensive path
        logger.warning("Flask instrumentation failed: %s", exc)


def add_span_attributes(**attributes):
    """
    Add attributes to the current span if one is active.

    Args:
        **attributes: Span attributes to attach.
    """
    current_span = trace.get_current_span()

    if current_span is None or not current_span.is_recording():
        return

    for key, value in attributes.items():
        if value is not None:
            current_span.set_attribute(key, value)

# Made with Bob
