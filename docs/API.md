# API Documentation

This document provides detailed information about the API endpoints available in the OpenTelemetry AI Tracing prototype.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health Check](#health-check)
  - [LLM Completion](#llm-completion)
  - [RAG Query](#rag-query)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Base URL

When running locally:
```
http://localhost:5000
```

## Authentication

Currently, the API does not require authentication. This is a prototype for local development and testing.

**Note:** In a production environment, you should implement proper authentication and authorization.

## Endpoints

### Health Check

Check if the application is running and healthy.

#### Request

```http
GET /health
```

#### Response

**Status Code:** `200 OK`

```json
{
  "status": "healthy",
  "service": "ai-tracing-prototype",
  "timestamp": "2024-01-15T10:30:00.123Z"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Health status (always "healthy" if responding) |
| `service` | string | Service name from configuration |
| `timestamp` | string | ISO 8601 timestamp of the response |

#### Example

```bash
curl http://localhost:5000/health
```

---

### LLM Completion

Generate a text completion using the local LLM (Ollama).

#### Request

```http
POST /api/llm/complete
Content-Type: application/json
```

#### Request Body

```json
{
  "prompt": "What is OpenTelemetry?",
  "model": "llama2",
  "max_tokens": 100,
  "temperature": 0.7
}
```

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | - | The input prompt for the LLM |
| `model` | string | No | `llama2` | Model name to use (must be pulled in Ollama) |
| `max_tokens` | integer | No | unlimited | Maximum tokens to generate |
| `temperature` | float | No | `0.7` | Sampling temperature (0.0 to 1.0) |

#### Response

**Status Code:** `200 OK`

```json
{
  "completion": "OpenTelemetry is an observability framework for cloud-native software...",
  "model": "llama2",
  "tokens": 85,
  "prompt_tokens": 10,
  "completion_tokens": 75,
  "latency_ms": 1234
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `completion` | string | The generated text completion |
| `model` | string | Model used for generation |
| `tokens` | integer | Total tokens used (prompt + completion) |
| `prompt_tokens` | integer | Number of tokens in the prompt |
| `completion_tokens` | integer | Number of tokens in the completion |
| `latency_ms` | integer | Time taken in milliseconds |

#### Error Responses

**Status Code:** `400 Bad Request`

```json
{
  "error": "Missing required field: prompt"
}
```

**Status Code:** `503 Service Unavailable`

```json
{
  "error": "Ollama not available",
  "message": "Failed to connect to Ollama at http://localhost:11434",
  "suggestion": "Please ensure Ollama is running: ollama serve"
}
```

**Status Code:** `503 Service Unavailable`

```json
{
  "error": "Model not available",
  "message": "Model 'llama2' is not available",
  "available_models": ["mistral:latest"],
  "suggestion": "Pull the model first: ollama pull llama2"
}
```

#### Examples

**Basic completion:**

```bash
curl -X POST http://localhost:5000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is OpenTelemetry?"
  }'
```

**With custom parameters:**

```bash
curl -X POST http://localhost:5000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain tracing in one sentence.",
    "model": "llama2",
    "max_tokens": 50,
    "temperature": 0.3
  }'
```

**Using Python:**

```python
import requests

response = requests.post(
    "http://localhost:5000/api/llm/complete",
    json={
        "prompt": "What is OpenTelemetry?",
        "max_tokens": 100
    }
)

result = response.json()
print(result["completion"])
```

---

### RAG Ingest
+
+Load documents into the RAG collection using the running application process.
+
+#### Request
+
+```http
+POST /api/rag/ingest
+Content-Type: application/json
+```
+
+#### Request Body
+
+```json
+{
+  "file_path": "data/sample_docs.txt",
+  "chunk_size": 500,
+  "overlap": 50
+}
+```
+
+#### Request Parameters
+
+| Parameter | Type | Required | Default | Description |
+|-----------|------|----------|---------|-------------|
+| `file_path` | string | Yes | - | Path to the document file to ingest |
+| `chunk_size` | integer | No | `500` | Maximum chunk size in characters |
+| `overlap` | integer | No | `50` | Character overlap between chunks |
+
+#### Response
+
+**Status Code:** `200 OK`
+
+```json
+{
+  "success": true,
+  "chunks_count": 10,
+  "collection": "documents",
+  "latency_ms": 123
+}
+```
+
+#### Example
+
+```bash
+curl -X POST http://localhost:5000/api/rag/ingest \
+  -H "Content-Type: application/json" \
+  -d '{
+    "file_path": "data/sample_docs.txt"
+  }'
+```
+
+---
+
+### RAG Query

Perform a Retrieval-Augmented Generation query using vector search and LLM.

#### Request

```http
POST /api/rag/query
Content-Type: application/json
```

#### Request Body

```json
{
  "query": "How does tracing work?",
  "top_k": 3,
  "min_score": 0.5,
  "model": "llama2",
  "max_tokens": 200
}
```

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | The search query |
| `top_k` | integer | No | `3` | Number of documents to retrieve |
| `min_score` | float | No | `0.0` | Minimum similarity score (0.0 to 1.0) |
| `model` | string | No | `llama2` | LLM model to use for answer generation |
| `max_tokens` | integer | No | unlimited | Maximum tokens for the answer |

#### Response

**Status Code:** `200 OK`

```json
{
  "query": "How does tracing work?",
  "retrieved_docs": [
    {
      "text": "Tracing allows you to track requests as they flow through distributed systems...",
      "score": 0.95,
      "metadata": {
        "source": "data/sample_docs.txt",
        "chunk_index": 2
      }
    },
    {
      "text": "Each trace consists of one or more spans representing operations...",
      "score": 0.87,
      "metadata": {
        "source": "data/sample_docs.txt",
        "chunk_index": 3
      }
    }
  ],
  "answer": "Based on the documentation, tracing works by tracking requests as they flow through distributed systems. Each trace consists of spans that represent individual operations...",
  "model": "llama2",
  "tokens": 120,
  "latency_ms": 2345
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | The original query |
| `retrieved_docs` | array | List of retrieved documents |
| `retrieved_docs[].text` | string | Document text content |
| `retrieved_docs[].score` | float | Similarity score (0.0 to 1.0) |
| `retrieved_docs[].metadata` | object | Document metadata |
| `answer` | string | Generated answer from the LLM |
| `model` | string | Model used for generation |
| `tokens` | integer | Total tokens used |
| `latency_ms` | integer | Total time taken in milliseconds |

#### Error Responses

**Status Code:** `400 Bad Request`

```json
{
  "error": "Missing required field: query"
}
```

**Status Code:** `500 Internal Server Error`

```json
{
  "error": "RAG query failed",
  "message": "Failed to perform vector search: Database error"
}
```

#### Examples

**Basic RAG query:**

```bash
curl -X POST http://localhost:5000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does tracing work?"
  }'
```

**With custom parameters:**

```bash
curl -X POST http://localhost:5000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is OpenTelemetry?",
    "top_k": 5,
    "min_score": 0.7,
    "max_tokens": 150
  }'
```

**Using Python:**

```python
import requests

response = requests.post(
    "http://localhost:5000/api/rag/query",
    json={
        "query": "How does tracing work?",
        "top_k": 3
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Retrieved {len(result['retrieved_docs'])} documents")
```

**Using JavaScript (fetch):**

```javascript
fetch('http://localhost:5000/api/rag/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'How does tracing work?',
    top_k: 3
  })
})
  .then(response => response.json())
  .then(data => {
    console.log('Answer:', data.answer);
    console.log('Retrieved docs:', data.retrieved_docs.length);
  });
```

---

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "suggestion": "How to fix the error (optional)"
}
```

### Common HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| `200` | OK | Request succeeded |
| `400` | Bad Request | Missing or invalid parameters |
| `500` | Internal Server Error | Unexpected server error |
| `503` | Service Unavailable | Ollama not running or model not available |

### Error Handling Best Practices

1. **Always check the status code** before processing the response
2. **Read the error message** for specific details
3. **Follow suggestions** provided in error responses
4. **Implement retries** for transient errors (503)
5. **Log errors** for debugging

### Example Error Handling (Python)

```python
import requests
import time

def call_llm_with_retry(prompt, max_retries=3):
    """Call LLM endpoint with retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:5000/api/llm/complete",
                json={"prompt": prompt},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                # Service unavailable, retry
                print(f"Service unavailable, retrying... (attempt {attempt + 1})")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                # Other error, don't retry
                error = response.json()
                raise Exception(f"API error: {error.get('message', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    
    raise Exception("Max retries exceeded")
```

---

## Rate Limiting

Currently, there is no rate limiting implemented. This is a prototype for local development.

**Note:** In a production environment, you should implement rate limiting to prevent abuse.

---

## Tracing

All API endpoints automatically generate OpenTelemetry traces that are exported to OpenLLMetry. You can view these traces in your OpenLLMetry dashboard.

### Trace Attributes

Each trace includes relevant attributes:

**LLM Completion traces:**
- `llm.model`: Model name
- `llm.prompt_length`: Length of the prompt
- `llm.completion_length`: Length of the completion
- `llm.total_tokens`: Total tokens used
- `llm.temperature`: Sampling temperature
- `llm.latency_ms`: Time taken

**RAG Query traces:**
- `rag.query`: The search query
- `rag.top_k`: Number of documents requested
- `rag.results_count`: Number of documents retrieved
- `rag.context_length`: Length of assembled context
- `rag.latency_ms`: Time taken

### Viewing Traces

1. Make API requests to generate traces
2. Open your OpenLLMetry dashboard
3. Navigate to the Traces section
4. Click on a trace to see detailed span information

---

## Performance Considerations

### Expected Latencies

- **Health Check**: < 10ms
- **LLM Completion**: 1-5 seconds (depends on model and prompt length)
- **RAG Query**: 2-8 seconds (includes vector search + LLM generation)

### Optimization Tips

1. **Use smaller models** for faster responses (e.g., `llama2` vs `llama2:70b`)
2. **Limit max_tokens** to reduce generation time
3. **Adjust top_k** in RAG queries to balance quality and speed
4. **Use lower temperature** for more deterministic (faster) responses
5. **Consider caching** frequently asked questions

---

## Testing the API

### Using curl

See examples above for each endpoint.

### Using Postman

1. Import the following collection:
   - Create a new collection
   - Add requests for each endpoint
   - Set the base URL to `http://localhost:5000`

### Using the Test Script

Run the provided test script:

```bash
uv run python test_llm_endpoint.py
```

---

## Additional Resources

- [Setup Guide](SETUP.md) - Installation and configuration
- [Language Implementation Guide](LANGUAGES.md) - Adapting to other languages
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)

---

**Made with Bob**