"""
Tests for Phase 2 telemetry integration.
"""

from unittest.mock import MagicMock

from app import create_app
from app.config import Config
from app.telemetry import add_span_attributes


def test_health_endpoint_returns_service_name():
    """Health endpoint should expose the configured service name."""
    app = create_app()

    with app.test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == Config.OTEL_SERVICE_NAME
    assert "timestamp" in data


def test_add_span_attributes_sets_values_on_active_span(mocker):
    """Span attributes should be added when a recording span is active."""
    mock_span = MagicMock()
    mock_span.is_recording.return_value = True

    mocker.patch("app.telemetry.trace.get_current_span", return_value=mock_span)

    add_span_attributes(**{
        "service.name": "ai-tracing-prototype",
        "request.type": "health_check",
    })

    mock_span.set_attribute.assert_any_call("service.name", "ai-tracing-prototype")
    mock_span.set_attribute.assert_any_call("request.type", "health_check")


def test_add_span_attributes_skips_non_recording_span(mocker):
    """No attributes should be added when the span is not recording."""
    mock_span = MagicMock()
    mock_span.is_recording.return_value = False

    mocker.patch("app.telemetry.trace.get_current_span", return_value=mock_span)

    add_span_attributes(**{"service.name": "ignored"})

    mock_span.set_attribute.assert_not_called()

# Made with Bob
