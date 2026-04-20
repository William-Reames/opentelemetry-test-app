"""
Unit tests for LLM service.

These tests verify the LLM service functionality including completion generation
and error handling. Tests use mocking to avoid requiring a running Ollama instance.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.llm_service import OllamaServiceError, generate_completion


class TestGenerateCompletion:
    """Tests for the generate_completion function."""

    @patch("app.llm_service.ChatOllama")
    @patch("app.llm_service.trace.get_current_span")
    def test_successful_completion(self, mock_span, mock_chat_ollama_class):
        """Test successful completion generation with ChatOllama."""
        # Setup mocks
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "OpenTelemetry is an observability framework."
        mock_response.response_metadata = {
            "prompt_eval_count": 10,
            "eval_count": 15,
        }
        mock_llm.invoke.return_value = mock_response
        mock_chat_ollama_class.return_value = mock_llm

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
        assert result["latency_ms"] >= 0

        # Verify ChatOllama was created with correct parameters
        mock_chat_ollama_class.assert_called_once()
        call_kwargs = mock_chat_ollama_class.call_args[1]
        assert call_kwargs["model"] == "llama2"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["num_predict"] == 50

        # Verify span attributes were set
        mock_current_span.set_attribute.assert_any_call("llm.model", "llama2")
        mock_current_span.set_attribute.assert_any_call("llm.total_tokens", 25)

    @patch("app.llm_service.ChatOllama")
    @patch("app.llm_service.trace.get_current_span")
    def test_completion_with_defaults(self, mock_span, mock_chat_ollama_class):
        """Test completion with default parameters."""
        # Setup mocks
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_response.response_metadata = {
            "prompt_eval_count": 5,
            "eval_count": 10,
        }
        mock_llm.invoke.return_value = mock_response
        mock_chat_ollama_class.return_value = mock_llm

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = False
        mock_span.return_value = mock_current_span

        # Execute (no model specified, should use default)
        result = generate_completion(prompt="Test prompt")

        # Verify
        assert "completion" in result
        assert result["completion"] == "Test response"
        assert "model" in result
        assert result["tokens"] == 15

        # Verify ChatOllama was created without num_predict (no max_tokens)
        call_kwargs = mock_chat_ollama_class.call_args[1]
        assert "num_predict" not in call_kwargs

    @patch("app.llm_service.ChatOllama")
    @patch("app.llm_service.trace.get_current_span")
    def test_completion_failure(self, mock_span, mock_chat_ollama_class):
        """Test handling of completion failure."""
        # Setup mock to raise exception
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("Model not found")
        mock_chat_ollama_class.return_value = mock_llm

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = True
        mock_span.return_value = mock_current_span

        # Execute and verify exception
        with pytest.raises(OllamaServiceError) as exc_info:
            generate_completion(prompt="Test prompt")

        assert "Model not found" in str(exc_info.value)

        # Verify error attributes were set on span
        mock_current_span.set_attribute.assert_any_call("error", True)

    @patch("app.llm_service.ChatOllama")
    @patch("app.llm_service.trace.get_current_span")
    def test_handles_missing_metadata(self, mock_span, mock_chat_ollama_class):
        """Test handling of response without token metadata."""
        # Setup mock with response that has no metadata
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test completion"
        mock_response.response_metadata = {}  # No token counts
        mock_llm.invoke.return_value = mock_response
        mock_chat_ollama_class.return_value = mock_llm

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = False
        mock_span.return_value = mock_current_span

        # Execute
        result = generate_completion(prompt="Test")

        # Verify - should handle missing metadata gracefully
        assert result["completion"] == "Test completion"
        assert result["tokens"] == 0  # No token counts available
        assert result["prompt_tokens"] == 0
        assert result["completion_tokens"] == 0

    @patch("app.llm_service.ChatOllama")
    @patch("app.llm_service.trace.get_current_span")
    def test_completion_with_none_token_counts(self, mock_span, mock_chat_ollama_class):
        """Test handling of None values in token counts."""
        # Setup mock with None token counts
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test"
        mock_response.response_metadata = {
            "prompt_eval_count": None,
            "eval_count": None,
        }
        mock_llm.invoke.return_value = mock_response
        mock_chat_ollama_class.return_value = mock_llm

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = False
        mock_span.return_value = mock_current_span

        # Execute
        result = generate_completion(prompt="Test")

        # Verify - should handle None values
        assert result["tokens"] == 0
        assert result["prompt_tokens"] == 0
        assert result["completion_tokens"] == 0


# Made with Bob
