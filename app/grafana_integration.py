"""Grafana/Prometheus integration."""

import logging
from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

logger = logging.getLogger(__name__)

def initialize_grafana_telemetry(app):
    """Initialize Prometheus metrics integration."""
    
    # Configure Prometheus (metrics)
    try:
        metric_reader = PrometheusMetricReader()
        meter_provider = MeterProvider(metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        
        # Add Prometheus metrics endpoint
        app.wsgi_app = DispatcherMiddleware(
            app.wsgi_app,
            {'/metrics': make_wsgi_app()}
        )
        logger.info("Prometheus metrics endpoint configured at /metrics")
    except Exception as exc:
        logger.error(f"Failed to configure Prometheus: {exc}")

# Made with Bob