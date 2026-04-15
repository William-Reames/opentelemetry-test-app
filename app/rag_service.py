"""
RAG service for vector search and retrieval-augmented generation.

This module provides functions for document ingestion, vector search using ChromaDB,
and RAG query processing with proper error handling and tracing integration.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from opentelemetry import trace
from traceloop.sdk.decorators import task, workflow

from app.config import Config
from app.llm_service import generate_completion

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class RAGServiceError(Exception):
    """Raised when a RAG service operation fails."""


# Global ChromaDB client (initialized once)
_chroma_client: Optional[chromadb.Client] = None
_collection: Optional[chromadb.Collection] = None


def _get_chroma_client() -> chromadb.Client:
    """
    Get or create the ChromaDB client (singleton pattern).
    
    Returns:
        ChromaDB client instance.
    """
    global _chroma_client
    
    if _chroma_client is None:
        logger.info("Initializing ChromaDB client with persist directory: %s", Config.CHROMA_PERSIST_DIR)
        
        # Ensure the persist directory exists
        os.makedirs(Config.CHROMA_PERSIST_DIR, exist_ok=True)
        
        _chroma_client = chromadb.Client(
            Settings(
                persist_directory=Config.CHROMA_PERSIST_DIR,
                anonymized_telemetry=False,
            )
        )
        logger.info("ChromaDB client initialized successfully")
    
    return _chroma_client


def _get_or_create_collection() -> chromadb.Collection:
    """
    Get or create the ChromaDB collection.
    
    Returns:
        ChromaDB collection instance.
    """
    global _collection
    
    if _collection is None:
        client = _get_chroma_client()
        
        logger.info("Getting or creating collection: %s", Config.CHROMA_COLLECTION)
        _collection = client.get_or_create_collection(
            name=Config.CHROMA_COLLECTION,
            metadata={"description": "Documents for RAG queries"}
        )
        logger.info("Collection ready: %s (count: %d)", Config.CHROMA_COLLECTION, _collection.count())
    
    return _collection


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: The text to chunk.
        chunk_size: Maximum size of each chunk in characters.
        overlap: Number of characters to overlap between chunks.
    
    Returns:
        List of text chunks.
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary if possible
        if end < text_length:
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size // 2:  # Only break if we're past halfway
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return [c for c in chunks if c]  # Filter empty chunks


@task(name="ingest_documents")
def ingest_documents(file_path: str, chunk_size: int = 500, overlap: int = 50) -> Dict[str, Any]:
    """
    Ingest documents from a file into ChromaDB.
    
    Reads the file, splits it into chunks, generates embeddings, and stores
    them in the ChromaDB collection.
    
    Args:
        file_path: Path to the document file.
        chunk_size: Maximum size of each chunk in characters.
        overlap: Number of characters to overlap between chunks.
    
    Returns:
        Dict containing:
        - success (bool): Whether ingestion succeeded
        - chunks_count (int): Number of chunks created
        - collection (str): Collection name
        - error (str, optional): Error message if failed
    
    Raises:
        RAGServiceError: If ingestion fails.
    """
    start_time = time.time()
    
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("rag.file_path", file_path)
        current_span.set_attribute("rag.chunk_size", chunk_size)
        current_span.set_attribute("rag.overlap", overlap)
    
    try:
        # Read the file
        logger.info("Reading documents from: %s", file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Split into chunks
        logger.info("Chunking text (size: %d, overlap: %d)", chunk_size, overlap)
        chunks = _chunk_text(text, chunk_size, overlap)
        
        if current_span and current_span.is_recording():
            current_span.set_attribute("rag.chunks_count", len(chunks))
            current_span.set_attribute("rag.total_chars", len(text))
        
        # Get collection
        collection = _get_or_create_collection()
        
        # Prepare documents for ingestion
        ids = [f"doc_{i}" for i in range(len(chunks))]
        metadatas = [{"source": file_path, "chunk_index": i} for i in range(len(chunks))]
        
        # Add to collection (ChromaDB will auto-generate embeddings)
        logger.info("Adding %d chunks to collection: %s", len(chunks), Config.CHROMA_COLLECTION)
        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if current_span and current_span.is_recording():
            current_span.set_attribute("rag.latency_ms", latency_ms)
        
        logger.info("Successfully ingested %d chunks in %dms", len(chunks), latency_ms)
        return {
            "success": True,
            "chunks_count": len(chunks),
            "collection": Config.CHROMA_COLLECTION,
            "latency_ms": latency_ms,
        }
    
    except Exception as exc:
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Failed to ingest documents: {exc}"
        logger.exception("%s", error_msg)
        
        if current_span and current_span.is_recording():
            current_span.set_attribute("error", True)
            current_span.set_attribute("error.message", error_msg)
            current_span.set_attribute("rag.latency_ms", latency_ms)
        
        raise RAGServiceError(error_msg) from exc


@task(name="vector_search")
def vector_search(query: str, top_k: int = 3, min_score: float = 0.0) -> Dict[str, Any]:
    """
    Perform vector similarity search.
    
    Args:
        query: The search query.
        top_k: Number of results to return.
        min_score: Minimum similarity score threshold (0.0 to 1.0).
    
    Returns:
        Dict containing:
        - documents (list): Retrieved documents with text and scores
        - count (int): Number of results
        - query (str): Original query
        - latency_ms (int): Search latency
    
    Raises:
        RAGServiceError: If search fails.
    """
    start_time = time.time()
    
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("rag.query", query)
        current_span.set_attribute("rag.top_k", top_k)
        current_span.set_attribute("rag.min_score", min_score)
        current_span.set_attribute("rag.collection", Config.CHROMA_COLLECTION)
    
    try:
        collection = _get_or_create_collection()
        
        logger.info("Performing vector search for query: '%s' (top_k=%d)", query[:50], top_k)
        
        # Query the collection
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
        )
        
        # Process results
        documents = []
        if results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                # ChromaDB returns distances, convert to similarity scores
                # Lower distance = higher similarity
                distance = results['distances'][0][i] if results['distances'] else 0
                # Convert distance to similarity score (1 - normalized_distance)
                # Assuming cosine distance, score = 1 - distance
                score = max(0.0, 1.0 - distance)
                
                if score >= min_score:
                    documents.append({
                        "text": doc,
                        "score": round(score, 4),
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    })
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if current_span and current_span.is_recording():
            current_span.set_attribute("rag.results_count", len(documents))
            current_span.set_attribute("rag.latency_ms", latency_ms)
        
        logger.info("Vector search completed: %d results in %dms", len(documents), latency_ms)
        return {
            "documents": documents,
            "count": len(documents),
            "query": query,
            "latency_ms": latency_ms,
        }
    
    except Exception as exc:
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Failed to perform vector search: {exc}"
        logger.exception("%s", error_msg)
        
        if current_span and current_span.is_recording():
            current_span.set_attribute("error", True)
            current_span.set_attribute("error.message", error_msg)
            current_span.set_attribute("rag.latency_ms", latency_ms)
        
        raise RAGServiceError(error_msg) from exc


@task(name="assemble_context")
def assemble_context(documents: List[Dict[str, Any]], query: str) -> str:
    """
    Assemble retrieved documents into context for the LLM.
    
    Args:
        documents: List of retrieved documents with text and scores.
        query: The original query.
    
    Returns:
        Formatted context string for the LLM prompt.
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("rag.documents_count", len(documents))
    
    if not documents:
        return "No relevant documents found."
    
    context_parts = ["Based on the following information:\n"]
    
    for i, doc in enumerate(documents, 1):
        context_parts.append(f"\n[Document {i}] (relevance: {doc['score']:.2f})")
        context_parts.append(doc['text'])
    
    context_parts.append(f"\n\nQuestion: {query}")
    context_parts.append("\nAnswer:")
    
    context = "\n".join(context_parts)
    
    if current_span and current_span.is_recording():
        current_span.set_attribute("rag.context_length", len(context))
    
    return context


@workflow(name="rag_query_workflow")
def query_with_rag(
    query: str,
    top_k: int = 3,
    min_score: float = 0.0,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Perform a complete RAG query workflow.
    
    This function orchestrates the full RAG pipeline:
    1. Vector search to retrieve relevant documents
    2. Context assembly from retrieved documents
    3. LLM generation with augmented context
    
    Args:
        query: The user's query.
        top_k: Number of documents to retrieve.
        min_score: Minimum similarity score threshold.
        model: LLM model to use (optional).
        max_tokens: Maximum tokens for LLM response (optional).
    
    Returns:
        Dict containing:
        - query (str): Original query
        - retrieved_docs (list): Retrieved documents
        - answer (str): Generated answer
        - latency_ms (int): Total latency
        - error (str, optional): Error message if failed
    """
    start_time = time.time()
    
    try:
        # Step 1: Vector search
        search_results = vector_search(query, top_k, min_score)
        retrieved_docs = search_results['documents']
        
        if not retrieved_docs:
            return {
                "query": query,
                "retrieved_docs": [],
                "answer": "I couldn't find any relevant information to answer your question.",
                "latency_ms": int((time.time() - start_time) * 1000),
            }
        
        # Step 2: Assemble context
        context = assemble_context(retrieved_docs, query)
        
        # Step 3: Generate answer with LLM
        completion_result = generate_completion(
            prompt=context,
            model=model,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        
        total_latency_ms = int((time.time() - start_time) * 1000)
        
        return {
            "query": query,
            "retrieved_docs": retrieved_docs,
            "answer": completion_result['completion'],
            "model": completion_result['model'],
            "tokens": completion_result['tokens'],
            "latency_ms": total_latency_ms,
        }
    
    except (RAGServiceError, Exception) as exc:
        total_latency_ms = int((time.time() - start_time) * 1000)
        error_msg = f"RAG query failed: {exc}"
        logger.exception("%s", error_msg)
        
        return {
            "query": query,
            "error": "RAG query failed",
            "message": str(exc),
            "latency_ms": total_latency_ms,
        }


def get_collection_stats() -> Dict[str, Any]:
    """
    Get statistics about the ChromaDB collection.
    
    Returns:
        Dict with collection statistics.
    """
    try:
        collection = _get_or_create_collection()
        count = collection.count()
        
        return {
            "collection": Config.CHROMA_COLLECTION,
            "document_count": count,
            "persist_directory": Config.CHROMA_PERSIST_DIR,
        }
    except Exception as exc:
        logger.exception("Failed to get collection stats: %s", exc)
        return {
            "error": str(exc)
        }


# Made with Bob