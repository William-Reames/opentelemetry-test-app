"""
Unit tests for LLM service.

These tests verify the LLM service functionality including connection checking,
completion generation, and error handling. Tests use mocking to avoid requiring
a running Ollama instance.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.llm_service import (
    OllamaServiceError,
    check_ollama_connection,
    complete_with_ollama,
    generate_completion,
)


class TestCheckOllamaConnection:
    """Tests for the check_ollama_connection function."""

    @patch("app.llm_service.ollama.Client")
    def test_connection_successful(self, mock_client_class):
        """Test successful connection to Ollama."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.list.return_value = {
            "models": [
                {"name": "llama2:latest"},
                {"name": "mistral:latest"},
            ]
        }
        mock_client_class.return_value = mock_client

        # Execute
        result = check_ollama_connection()

        # Verify
        assert result["available"] is True
        assert "llama2:latest" in result["models"]
        assert "mistral:latest" in result["models"]
        assert "host" in result

    @patch("app.llm_service.ollama.Client")
    def test_connection_failed(self, mock_client_class):
        """Test failed connection to Ollama."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.list.side_effect = Exception("Connection refused")
        mock_client_class.return_value = mock_client

        # Execute
        result = check_ollama_connection()

        # Verify
        assert result["available"] is False
        assert "error" in result
        assert "Connection refused" in result["error"]

    @patch("app.llm_service.ollama.Client")
    def test_handles_object_response(self, mock_client_class):
        """Test handling of object-based response from Ollama."""
        # Setup mock with object-like response
        mock_client = MagicMock()
        mock_model = MagicMock()
        mock_model.name = "llama2:latest"
        mock_model.model = "llama2:latest"  # Add model attribute too
        mock_response = MagicMock()
        mock_response.models = [mock_model]
        mock_client.list.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Execute
        result = check_ollama_connection()

        # Verify
        assert result["available"] is True
        assert "llama2:latest" in result["models"]


class TestGenerateCompletion:
    """Tests for the generate_completion function."""

    @patch("app.llm_service.ollama.Client")
    @patch("app.llm_service.trace.get_current_span")
    def test_successful_completion(self, mock_span, mock_client_class):
        """Test successful completion generation."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.generate.return_value = {
            "response": "OpenTelemetry is an observability framework.",
            "prompt_eval_count": 10,
            "eval_count": 15,
        }
        mock_client_class.return_value = mock_client

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = True
        mock_span.return_value = mock_current_span

        # Execute
        result = generate_completion(
            prompt="What is OpenTelemetry?",
            model="llama2",
            max_tokens=50,
            temperature=0.7,
        )

        # Verify
        assert result["completion"] == "OpenTelemetry is an observability framework."
        assert result["model"] == "llama2"
        assert result["tokens"] == 25  # 10 + 15
        assert result["prompt_tokens"] == 10
        assert result["completion_tokens"] == 15
        assert "latency_ms" in result
        assert result["latency_ms"] >= 0  # Can be 0 in fast tests

        # Verify span attributes were set
        mock_current_span.set_attribute.assert_any_call("llm.model", "llama2")
        mock_current_span.set_attribute.assert_any_call("llm.total_tokens", 25)

    @patch("app.llm_service.ollama.Client")
    @patch("app.llm_service.trace.get_current_span")
    def test_completion_with_defaults(self, mock_span, mock_client_class):
        """Test completion with default parameters."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.generate.return_value = {
            "response": "Test response",
            "prompt_eval_count": 5,
            "eval_count": 10,
        }
        mock_client_class.return_value = mock_client

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = False
        mock_span.return_value = mock_current_span

        # Execute (no model specified, should use default)
        result = generate_completion(prompt="Test prompt")

        # Verify
        assert "completion" in result
        assert "model" in result
        assert result["tokens"] == 15

    @patch("app.llm_service.ollama.Client")
    @patch("app.llm_service.trace.get_current_span")
    def test_completion_failure(self, mock_span, mock_client_class):
        """Test handling of completion failure."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.generate.side_effect = Exception("Model not found")
        mock_client_class.return_value = mock_client

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = True
        mock_span.return_value = mock_current_span

        # Execute and verify exception
        with pytest.raises(OllamaServiceError) as exc_info:
            generate_completion(prompt="Test prompt")

        assert "Model not found" in str(exc_info.value)

        # Verify error attributes were set on span
        mock_current_span.set_attribute.assert_any_call("error", True)

    @patch("app.llm_service.ollama.Client")
    @patch("app.llm_service.trace.get_current_span")
    def test_handles_object_response(self, mock_span, mock_client_class):
        """Test handling of object-based response from Ollama."""
        # Setup mock with object-like response that has model_dump method
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Configure model_dump to return a dict
        mock_response.model_dump.return_value = {
            "response": "Test completion",
            "prompt_eval_count": 8,
            "eval_count": 12,
        }
        mock_client.generate.return_value = mock_response
        mock_client_class.return_value = mock_client

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = False
        mock_span.return_value = mock_current_span

        # Execute
        result = generate_completion(prompt="Test")

        # Verify
        assert result["completion"] == "Test completion"
        assert result["tokens"] == 20


class TestCompleteWithOllama:
    """Tests for the complete_with_ollama workflow function."""

    @patch("app.llm_service.check_ollama_connection")
    @patch("app.llm_service.generate_completion")
    def test_successful_workflow(self, mock_generate, mock_check):
        """Test successful completion workflow."""
        # Setup mocks
        mock_check.return_value = {
            "available": True,
            "models": ["llama2:latest"],
        }
        mock_generate.return_value = {
            "completion": "Test response",
            "model": "llama2",
            "tokens": 20,
            "latency_ms": 1000,
        }

        # Execute
        result = complete_with_ollama(prompt="Test prompt", model="llama2")

        # Verify
        assert "completion" in result
        assert result["completion"] == "Test response"
        assert "error" not in result

    @patch("app.llm_service.check_ollama_connection")
    def test_ollama_not_available(self, mock_check):
        """Test workflow when Ollama is not available."""
        # Setup mock
        mock_check.return_value = {
            "available": False,
            "error": "Connection refused",
        }

        # Execute
        result = complete_with_ollama(prompt="Test prompt")

        # Verify
        assert "error" in result
        assert result["error"] == "Ollama not available"
        assert "suggestion" in result

    @patch("app.llm_service.check_ollama_connection")
    def test_model_not_available(self, mock_check):
        """Test workflow when requested model is not available."""
        # Setup mock
        mock_check.return_value = {
            "available": True,
            "models": ["llama2:latest", "mistral:latest"],
        }

        # Execute (request non-existent model)
        result = complete_with_ollama(prompt="Test prompt", model="gpt-4")

        # Verify
        assert "error" in result
        assert result["error"] == "Model not available"
        assert "available_models" in result
        assert "suggestion" in result

    @patch("app.llm_service.check_ollama_connection")
    @patch("app.llm_service.generate_completion")
    def test_model_matching_with_tags(self, mock_generate, mock_check):
        """Test that model matching works with and without tags."""
        # Setup mocks
        mock_check.return_value = {
            "available": True,
            "models": ["llama2:latest"],
        }
        mock_generate.return_value = {
            "completion": "Test",
            "model": "llama2",
            "tokens": 10,
            "latency_ms": 500,
        }

        # Execute with model name without tag
        result = complete_with_ollama(prompt="Test", model="llama2")

        # Verify - should succeed because llama2 matches llama2:latest
        assert "error" not in result
        assert "completion" in result

    @patch("app.llm_service.check_ollama_connection")
    @patch("app.llm_service.generate_completion")
    def test_completion_error_handling(self, mock_generate, mock_check):
        """Test handling of completion errors in workflow."""
        # Setup mocks
        mock_check.return_value = {
            "available": True,
            "models": ["llama2:latest"],
        }
        mock_generate.side_effect = OllamaServiceError("Generation failed")

        # Execute - specify model explicitly to match available models
        result = complete_with_ollama(prompt="Test prompt", model="llama2")

        # Verify
        assert "error" in result
        assert result["error"] == "Completion failed"
        assert "Generation failed" in result["message"]


# Made with Bob