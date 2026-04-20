"""
Telemetry initialization for the AI Tracing Prototype.

This module configures OpenTelemetry and Traceloop integration for Flask.
"""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from traceloop.sdk import Traceloop

_TRACING_INITIALIZED = False


def initialize_telemetry(app, config):
    """
    Initialize tracing for the Flask application.

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

    # Configure OpenTelemetry to export to Tempo
    try:
        resource = Resource.create({"service.name": config.OTEL_SERVICE_NAME})
        tracer_provider = TracerProvider(resource=resource)
        
        # Add OTLP exporter for Tempo
        otlp_exporter = OTLPSpanExporter(
            endpoint=config.TEMPO_ENDPOINT,
            insecure=True  # Use insecure for local development
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set the global tracer provider
        trace.set_tracer_provider(tracer_provider)
        logger.info("OpenTelemetry configured to export to Tempo at %s", config.TEMPO_ENDPOINT)
    except Exception as exc:
        logger.warning("Failed to configure Tempo exporter: %s", exc)

    # Initialize Traceloop if configured
    if Traceloop is None:
        logger.warning("Traceloop SDK is not installed; continuing without Traceloop.")
    elif not config.TRACELOOP_API_KEY:
        logger.warning("TRACELOOP_API_KEY is not set; continuing without Traceloop export.")
    else:
        try:
            Traceloop.init(
                app_name=config.OTEL_SERVICE_NAME,
                api_key=config.TRACELOOP_API_KEY,
                disable_batch=config.TRACELOOP_DISABLE_BATCH,
            )
            logger.info("Traceloop initialized for service '%s'.", config.OTEL_SERVICE_NAME)
        except Exception as exc:  # pragma: no cover - defensive path
            logger.warning("Traceloop initialization failed: %s", exc)

    try:
        FlaskInstrumentor().instrument_app(app)
        _TRACING_INITIALIZED = True
        logger.info("Flask OpenTelemetry instrumentation enabled.")
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
