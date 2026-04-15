"""
Unit tests for RAG service.

These tests verify the RAG service functionality including document ingestion,
vector search, context assembly, and the complete RAG workflow. Tests use mocking
to avoid requiring a running ChromaDB instance.
"""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.rag_service import (
    RAGServiceError,
    _chunk_text,
    assemble_context,
    get_collection_stats,
    ingest_documents,
    query_with_rag,
    vector_search,
)


class TestChunkText:
    """Tests for the _chunk_text helper function."""

    def test_chunk_small_text(self):
        """Test chunking text smaller than chunk size."""
        text = "This is a small text."
        chunks = _chunk_text(text, chunk_size=100, overlap=10)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_large_text(self):
        """Test chunking text larger than chunk size."""
        text = "A" * 1000
        chunks = _chunk_text(text, chunk_size=100, overlap=10)

        assert len(chunks) > 1
        # Check overlap exists
        assert chunks[0][-10:] == chunks[1][:10]

    def test_chunk_with_sentence_boundaries(self):
        """Test that chunking respects sentence boundaries."""
        text = "First sentence. " * 50  # Create text with clear boundaries
        chunks = _chunk_text(text, chunk_size=100, overlap=10)

        # Most chunks should end with a period
        chunks_ending_with_period = sum(1 for c in chunks if c.endswith('.'))
        assert chunks_ending_with_period >= len(chunks) // 2

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunks = _chunk_text("", chunk_size=100, overlap=10)
        assert len(chunks) == 0

    def test_chunk_with_newlines(self):
        """Test chunking text with newlines."""
        text = "Line 1\n" * 100
        chunks = _chunk_text(text, chunk_size=100, overlap=10)

        assert len(chunks) > 1
        # Should break at newlines when possible
        assert any('\n' in chunk for chunk in chunks)


class TestIngestDocuments:
    """Tests for the ingest_documents function."""

    @patch("app.rag_service._get_or_create_collection")
    @patch("app.rag_service.trace.get_current_span")
    @patch("builtins.open", new_callable=mock_open, read_data="Sample document text.")
    def test_successful_ingestion(self, mock_file, mock_span, mock_collection):
        """Test successful document ingestion."""
        # Setup mocks
        mock_coll = MagicMock()
        mock_coll.add = MagicMock()
        mock_collection.return_value = mock_coll

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = True
        mock_span.return_value = mock_current_span

        # Execute
        result = ingest_documents("test.txt", chunk_size=100, overlap=10)

        # Verify
        assert result["success"] is True
        assert result["chunks_count"] >= 1
        assert "collection" in result
        assert "latency_ms" in result

        # Verify collection.add was called
        mock_coll.add.assert_called_once()

    @patch("app.rag_service._get_or_create_collection")
    @patch("app.rag_service.trace.get_current_span")
    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_ingestion_file_not_found(self, mock_file, mock_span, mock_collection):
        """Test ingestion with non-existent file."""
        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = True
        mock_span.return_value = mock_current_span

        # Execute and verify exception
        with pytest.raises(RAGServiceError) as exc_info:
            ingest_documents("nonexistent.txt")

        assert "File not found" in str(exc_info.value)

    @patch("app.rag_service._get_or_create_collection")
    @patch("app.rag_service.trace.get_current_span")
    @patch("builtins.open", new_callable=mock_open, read_data="Test content")
    def test_ingestion_with_large_chunks(self, mock_file, mock_span, mock_collection):
        """Test ingestion with custom chunk parameters."""
        mock_coll = MagicMock()
        mock_collection.return_value = mock_coll

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = False
        mock_span.return_value = mock_current_span

        # Execute with custom parameters
        result = ingest_documents("test.txt", chunk_size=1000, overlap=100)

        # Verify
        assert result["success"] is True


class TestVectorSearch:
    """Tests for the vector_search function."""

    @patch("app.rag_service._get_or_create_collection")
    @patch("app.rag_service.trace.get_current_span")
    def test_successful_search(self, mock_span, mock_collection):
        """Test successful vector search."""
        # Setup mocks
        mock_coll = MagicMock()
        mock_coll.query.return_value = {
            'documents': [['Document 1', 'Document 2']],
            'distances': [[0.1, 0.3]],
            'metadatas': [[{'source': 'test.txt'}, {'source': 'test.txt'}]]
        }
        mock_collection.return_value = mock_coll

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = True
        mock_span.return_value = mock_current_span

        # Execute
        result = vector_search("test query", top_k=2, min_score=0.0)

        # Verify
        assert result["count"] == 2
        assert len(result["documents"]) == 2
        assert result["documents"][0]["text"] == "Document 1"
        assert result["documents"][0]["score"] > result["documents"][1]["score"]
        assert "latency_ms" in result

    @patch("app.rag_service._get_or_create_collection")
    @patch("app.rag_service.trace.get_current_span")
    def test_search_with_min_score_filter(self, mock_span, mock_collection):
        """Test vector search with minimum score filtering."""
        # Setup mocks
        mock_coll = MagicMock()
        mock_coll.query.return_value = {
            'documents': [['Doc 1', 'Doc 2', 'Doc 3']],
            'distances': [[0.1, 0.5, 0.9]],  # Scores: 0.9, 0.5, 0.1
            'metadatas': [[{}, {}, {}]]
        }
        mock_collection.return_value = mock_coll

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = False
        mock_span.return_value = mock_current_span

        # Execute with min_score filter
        result = vector_search("test query", top_k=3, min_score=0.6)

        # Verify - only documents with score >= 0.6 should be returned
        assert result["count"] == 1
        assert result["documents"][0]["score"] >= 0.6

    @patch("app.rag_service._get_or_create_collection")
    @patch("app.rag_service.trace.get_current_span")
    def test_search_no_results(self, mock_span, mock_collection):
        """Test vector search with no results."""
        # Setup mocks
        mock_coll = MagicMock()
        mock_coll.query.return_value = {
            'documents': [[]],
            'distances': [[]],
            'metadatas': [[]]
        }
        mock_collection.return_value = mock_coll

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = False
        mock_span.return_value = mock_current_span

        # Execute
        result = vector_search("test query", top_k=3)

        # Verify
        assert result["count"] == 0
        assert len(result["documents"]) == 0

    @patch("app.rag_service._get_or_create_collection")
    @patch("app.rag_service.trace.get_current_span")
    def test_search_failure(self, mock_span, mock_collection):
        """Test handling of search failure."""
        # Setup mock to raise exception
        mock_coll = MagicMock()
        mock_coll.query.side_effect = Exception("Database error")
        mock_collection.return_value = mock_coll

        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = True
        mock_span.return_value = mock_current_span

        # Execute and verify exception
        with pytest.raises(RAGServiceError) as exc_info:
            vector_search("test query")

        assert "Database error" in str(exc_info.value)


class TestAssembleContext:
    """Tests for the assemble_context function."""

    @patch("app.rag_service.trace.get_current_span")
    def test_assemble_with_documents(self, mock_span):
        """Test context assembly with documents."""
        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = True
        mock_span.return_value = mock_current_span

        documents = [
            {"text": "Document 1 content", "score": 0.95},
            {"text": "Document 2 content", "score": 0.85},
        ]

        context = assemble_context(documents, "What is this?")

        # Verify
        assert "Document 1 content" in context
        assert "Document 2 content" in context
        assert "What is this?" in context
        assert "0.95" in context
        assert "0.85" in context

    @patch("app.rag_service.trace.get_current_span")
    def test_assemble_with_no_documents(self, mock_span):
        """Test context assembly with no documents."""
        mock_current_span = MagicMock()
        mock_current_span.is_recording.return_value = False
        mock_span.return_value = mock_current_span

        context = assemble_context([], "What is this?")

        # Verify
        assert context == "No relevant documents found."


class TestQueryWithRAG:
    """Tests for the query_with_rag workflow function."""

    @patch("app.rag_service.vector_search")
    @patch("app.rag_service.generate_completion")
    def test_successful_rag_query(self, mock_generate, mock_search):
        """Test successful RAG query workflow."""
        # Setup mocks
        mock_search.return_value = {
            "documents": [
                {"text": "Relevant doc", "score": 0.9}
            ],
            "count": 1,
            "latency_ms": 100,
        }

        mock_generate.return_value = {
            "completion": "This is the answer",
            "model": "llama2",
            "tokens": 20,
            "latency_ms": 500,
        }

        # Execute
        result = query_with_rag("What is this?", top_k=3)

        # Verify
        assert "answer" in result
        assert result["answer"] == "This is the answer"
        assert len(result["retrieved_docs"]) == 1
        assert "latency_ms" in result
        assert "error" not in result

    @patch("app.rag_service.vector_search")
    def test_rag_query_no_results(self, mock_search):
        """Test RAG query with no search results."""
        # Setup mock
        mock_search.return_value = {
            "documents": [],
            "count": 0,
            "latency_ms": 100,
        }

        # Execute
        result = query_with_rag("What is this?")

        # Verify
        assert "answer" in result
        assert "couldn't find" in result["answer"].lower()
        assert len(result["retrieved_docs"]) == 0

    @patch("app.rag_service.vector_search")
    @patch("app.rag_service.generate_completion")
    def test_rag_query_with_custom_parameters(self, mock_generate, mock_search):
        """Test RAG query with custom parameters."""
        # Setup mocks
        mock_search.return_value = {
            "documents": [{"text": "Doc", "score": 0.8}],
            "count": 1,
            "latency_ms": 100,
        }

        mock_generate.return_value = {
            "completion": "Answer",
            "model": "mistral",
            "tokens": 15,
            "latency_ms": 400,
        }

        # Execute with custom parameters
        result = query_with_rag(
            "Query",
            top_k=5,
            min_score=0.7,
            model="mistral",
            max_tokens=100
        )

        # Verify
        assert "answer" in result
        assert result["model"] == "mistral"

        # Verify search was called with correct parameters
        mock_search.assert_called_once_with("Query", 5, 0.7)

    @patch("app.rag_service.vector_search")
    def test_rag_query_search_failure(self, mock_search):
        """Test RAG query when search fails."""
        # Setup mock to raise exception
        mock_search.side_effect = RAGServiceError("Search failed")

        # Execute
        result = query_with_rag("What is this?")

        # Verify
        assert "error" in result
        assert "message" in result
        assert "Search failed" in result["message"]

    @patch("app.rag_service.vector_search")
    @patch("app.rag_service.generate_completion")
    def test_rag_query_generation_failure(self, mock_generate, mock_search):
        """Test RAG query when LLM generation fails."""
        # Setup mocks
        mock_search.return_value = {
            "documents": [{"text": "Doc", "score": 0.9}],
            "count": 1,
            "latency_ms": 100,
        }

        mock_generate.side_effect = Exception("Generation failed")

        # Execute
        result = query_with_rag("What is this?")

        # Verify
        assert "error" in result
        assert "Generation failed" in result["message"]


class TestGetCollectionStats:
    """Tests for the get_collection_stats function."""

    @patch("app.rag_service._get_or_create_collection")
    def test_get_stats_success(self, mock_collection):
        """Test successful retrieval of collection stats."""
        # Setup mock
        mock_coll = MagicMock()
        mock_coll.count.return_value = 42
        mock_collection.return_value = mock_coll

        # Execute
        result = get_collection_stats()

        # Verify
        assert result["document_count"] == 42
        assert "collection" in result
        assert "persist_directory" in result

    @patch("app.rag_service._get_or_create_collection")
    def test_get_stats_failure(self, mock_collection):
        """Test handling of stats retrieval failure."""
        # Setup mock to raise exception
        mock_collection.side_effect = Exception("Database error")

        # Execute
        result = get_collection_stats()

        # Verify
        assert "error" in result
        assert "Database error" in result["error"]


# Made with Bob
