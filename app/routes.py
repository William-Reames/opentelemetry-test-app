"""
API routes for the AI Tracing Prototype.

This module defines all API endpoints for the application.
"""

from datetime import datetime, timezone

from flask import jsonify, request

from app.llm_service import OllamaServiceError, generate_completion
from app.rag_service import get_collection_stats, ingest_documents, query_with_rag
from app.telemetry import add_span_attributes


def _json_error(error: str, message: str, status_code: int):
    """Create a consistent JSON error response."""
    return jsonify({"error": error, "message": message}), status_code


def _record_error_attributes(error_type: str, message: str | None = None):
    """Add common error attributes to the current span."""
    attributes = {"error": True, "error.type": error_type}
    if message is not None:
        attributes["error.message"] = message
    add_span_attributes(**attributes)


def register_routes(app):  # pylint: disable=too-many-statements
    """
    Register all routes with the Flask application.

    Args:
        app: Flask application instance.
    """

    @app.route("/health", methods=["GET"])
    def health_check():
        """
        Health check endpoint.

        Returns:
            JSON response with status and timestamp.
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        service_name = app.config.get("OTEL_SERVICE_NAME", "ai-tracing-prototype")

        add_span_attributes(
            **{
                "health.status": "healthy",
                "health.timestamp": timestamp,
                "service.name": service_name,
                "request.type": "health_check",
            }
        )

        return (
            jsonify(
                {
                    "status": "healthy",
                    "timestamp": timestamp,
                    "service": service_name,
                }
            ),
            200,
        )

    @app.route("/", methods=["GET"])
    def index():
        """
        Root endpoint with API information.

        Returns:
            JSON response with available endpoints.
        """
        return (
            jsonify(
                {
                    "service": "AI Tracing Prototype",
                    "version": "1.0.0",
                    "endpoints": {
                        "health": "/health (GET)",
                        "llm_complete": "/api/llm/complete (POST)",
                        "rag_query": "/api/rag/query (POST)",
                        "rag_ingest": "/api/rag/ingest (POST)",
                        "rag_stats": "/api/rag/stats (GET)",
                    },
                }
            ),
            200,
        )

    @app.route("/api/llm/complete", methods=["POST"])
    def llm_complete():  # pylint: disable=too-many-return-statements
        """
        LLM completion endpoint.

        Request body:
            {
                "prompt": "Your prompt here",
                "model": "llama2" (optional),
                "max_tokens": 100 (optional),
                "temperature": 0.7 (optional)
            }

        Returns:
            JSON response with completion or error.
        """
        if not request.is_json:
            return _json_error(
                "Invalid request",
                "Content-Type must be application/json",
                400,
            )

        data = request.get_json()

        if "prompt" not in data:
            return _json_error(
                "Missing required field",
                'Request must include "prompt" field',
                400,
            )

        prompt = data["prompt"]
        if not prompt or not isinstance(prompt, str):
            return _json_error(
                "Invalid prompt",
                "Prompt must be a non-empty string",
                400,
            )

        model = data.get("model")
        max_tokens = data.get("max_tokens")
        temperature = data.get("temperature", 0.7)

        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1:
            return _json_error(
                "Invalid temperature",
                "Temperature must be a number between 0 and 1",
                400,
            )

        add_span_attributes(
            **{
                "request.type": "llm_completion",
                "llm.prompt_length": len(prompt),
                "llm.model_requested": model or app.config.get("OLLAMA_MODEL", "llama2"),
            }
        )

        try:
            result = generate_completion(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            add_span_attributes(
                **{
                    "llm.completion_length": len(result.get("completion", "")),
                    "llm.total_tokens": result.get("tokens", 0),
                    "llm.latency_ms": result.get("latency_ms", 0),
                }
            )
            return jsonify(result), 200

        except OllamaServiceError as exc:
            _record_error_attributes("llm_error", str(exc))
            return _json_error("LLM service error", str(exc), 503)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _record_error_attributes("internal_error", str(exc))
            return _json_error("Internal error", str(exc), 500)

    @app.route("/api/rag/query", methods=["POST"])
    def rag_query():  # pylint: disable=too-many-return-statements
        """
        RAG query endpoint.

        Request body:
            {
                "query": "Your question here",
                "top_k": 3 (optional),
                "min_score": 0.0 (optional),
                "model": "llama2" (optional),
                "max_tokens": 200 (optional)
            }

        Returns:
            JSON response with retrieved documents and generated answer.
        """
        if not request.is_json:
            return _json_error(
                "Invalid request",
                "Content-Type must be application/json",
                400,
            )

        data = request.get_json()

        if "query" not in data:
            return _json_error(
                "Missing required field",
                'Request must include "query" field',
                400,
            )

        query = data["query"]
        if not query or not isinstance(query, str):
            return _json_error(
                "Invalid query",
                "Query must be a non-empty string",
                400,
            )

        top_k = data.get("top_k", 3)
        min_score = data.get("min_score", 0.0)
        model = data.get("model")
        max_tokens = data.get("max_tokens")

        if not isinstance(top_k, int) or top_k < 1 or top_k > 10:
            return _json_error(
                "Invalid top_k",
                "top_k must be an integer between 1 and 10",
                400,
            )

        if not isinstance(min_score, (int, float)) or min_score < 0 or min_score > 1:
            return _json_error(
                "Invalid min_score",
                "min_score must be a number between 0 and 1",
                400,
            )

        add_span_attributes(
            **{
                "request.type": "rag_query",
                "rag.query_length": len(query),
                "rag.top_k": top_k,
                "rag.min_score": min_score,
            }
        )

        try:
            result = query_with_rag(
                query=query,
                top_k=top_k,
                min_score=min_score,
                model=model,
                max_tokens=max_tokens,
            )

            if "error" in result:
                _record_error_attributes(result["error"])
                return jsonify(result), 500

            add_span_attributes(
                **{
                    "rag.retrieved_docs_count": len(result.get("retrieved_docs", [])),
                    "rag.answer_length": len(result.get("answer", "")),
                    "rag.total_latency_ms": result.get("latency_ms", 0),
                }
            )
            return jsonify(result), 200

        except Exception as exc:  # pylint: disable=broad-exception-caught
            _record_error_attributes("internal_error", str(exc))
            return _json_error("Internal error", str(exc), 500)

    @app.route("/api/rag/ingest", methods=["POST"])
    def rag_ingest():
        """
        Document ingestion endpoint.

        Request body:
            {
                "file_path": "path/to/documents.txt",
                "chunk_size": 500 (optional),
                "overlap": 50 (optional)
            }

        Returns:
            JSON response with ingestion results.
        """
        if not request.is_json:
            return _json_error(
                "Invalid request",
                "Content-Type must be application/json",
                400,
            )

        data = request.get_json()

        if "file_path" not in data:
            return _json_error(
                "Missing required field",
                'Request must include "file_path" field',
                400,
            )

        file_path = data["file_path"]
        chunk_size = data.get("chunk_size", 500)
        overlap = data.get("overlap", 50)

        add_span_attributes(
            **{
                "request.type": "rag_ingest",
                "rag.file_path": file_path,
                "rag.chunk_size": chunk_size,
                "rag.overlap": overlap,
            }
        )

        try:
            result = ingest_documents(
                file_path=file_path,
                chunk_size=chunk_size,
                overlap=overlap,
            )

            if "error" in result:
                _record_error_attributes("ingestion_failed")
                return jsonify(result), 500

            add_span_attributes(
                **{
                    "rag.chunks_ingested": result.get("chunks_count", 0),
                    "rag.ingestion_latency_ms": result.get("latency_ms", 0),
                }
            )
            return jsonify(result), 200

        except Exception as exc:  # pylint: disable=broad-exception-caught
            _record_error_attributes("internal_error", str(exc))
            return _json_error("Internal error", str(exc), 500)

    @app.route("/api/rag/stats", methods=["GET"])
    def rag_stats():
        """
        Get RAG collection statistics.

        Returns:
            JSON response with collection stats.
        """
        add_span_attributes(**{"request.type": "rag_stats"})

        try:
            stats = get_collection_stats()
            return jsonify(stats), 200

        except Exception as exc:  # pylint: disable=broad-exception-caught
            _record_error_attributes("internal_error", str(exc))
            return _json_error("Internal error", str(exc), 500)

    @app.errorhandler(404)
    def not_found(_error):
        """Handle 404 errors."""
        return _json_error("Not found", "The requested endpoint does not exist", 404)

    @app.errorhandler(500)
    def internal_error(_error):
        """Handle 500 errors."""
        return _json_error("Internal server error", "An unexpected error occurred", 500)


# Made with Bob
