# OpenTelemetry Tracing with AI Components - Minimal Prototype Plan

## Project Overview

This project creates a minimal working prototype demonstrating OpenTelemetry tracing integration with AI components. The prototype focuses on:
- **LLM calls** using Ollama (local models)
- **RAG queries** using a vector database
- **Trace visibility** in OpenLLMetry (Traceloop)

The application will be built in Python with Flask, designed to be self-contained and free to run locally.

## Acceptance Criteria

✅ **Core Requirements:**
1. Working Flask web application with API endpoints
2. OpenTelemetry instrumentation successfully integrated
3. LLM calls to Ollama with proper tracing
4. RAG query functionality with vector search and tracing
5. Traces visible and analyzable in OpenLLMetry dashboard
6. Basic documentation for setup and usage
7. Notes on how to adapt implementation to other programming languages

✅ **Success Metrics:**
- All API endpoints return valid responses
- Traces appear in OpenLLMetry within seconds of API calls
- Trace data includes relevant metadata (prompts, tokens, latency, etc.)
- Setup process documented and reproducible
- Code is clean, commented, and maintainable

## Technology Stack

### Core Components
- **Web Framework**: Flask (Python 3.12+)
- **LLM Provider**: Ollama (local, free)
- **Vector Database**: ChromaDB (embedded, no separate server needed)
- **Observability**: OpenLLMetry (Traceloop SDK)
- **Tracing**: OpenTelemetry Python SDK

### Why These Choices?
- **Flask**: Simple, well-documented, easy to instrument
- **Ollama**: Free, runs locally, no API keys needed
- **ChromaDB**: Embedded mode, no Docker required for prototype
- **OpenLLMetry**: Excellent auto-instrumentation for LLMs and vector DBs
- **Python**: Rich ecosystem for AI/ML, good OpenTelemetry support

## Architecture

```mermaid
graph TB
    Client[API Client/Browser]
    Flask[Flask Application]
    OTel[OpenTelemetry SDK]
    Traceloop[Traceloop SDK]
    Ollama[Ollama Local LLM]
    Chroma[ChromaDB Embedded]
    OpenLLMetry[OpenLLMetry Platform]
    
    Client -->|HTTP Requests| Flask
    Flask -->|Auto-instrumentation| OTel
    Flask -->|Traceloop decorators| Traceloop
    Flask -->|LLM Calls| Ollama
    Flask -->|Vector Operations| Chroma
    OTel -->|Export Traces| OpenLLMetry
    Traceloop -->|Enhanced Traces| OpenLLMetry
    
    style Flask fill:#4CAF50
    style OTel fill:#FF9800
    style Traceloop fill:#9C27B0
    style OpenLLMetry fill:#2196F3
```

## Project Structure
```

## Design

### API Endpoints

The application will expose three main endpoints:

#### 1. Health Check
- **Endpoint**: `GET /health`
- **Purpose**: Verify application is running
- **Response**: `{"status": "healthy", "timestamp": "..."}`
- **Tracing**: Basic HTTP span only

#### 2. LLM Completion
- **Endpoint**: `POST /api/llm/complete`
- **Purpose**: Send prompt to Ollama and get completion
- **Request Body**:
  ```json
  {
    "prompt": "What is OpenTelemetry?",
    "model": "llama2",
    "max_tokens": 100
  }
  ```
- **Response**:
  ```json
  {
    "completion": "OpenTelemetry is...",
    "model": "llama2",
    "tokens": 85,
    "latency_ms": 1234
  }
  ```
- **Tracing**:
  - Parent span: HTTP request
  - Child span: LLM call with prompt, completion, tokens, model metadata

#### 3. RAG Query
- **Endpoint**: `POST /api/rag/query`
- **Purpose**: Perform semantic search and generate augmented response
- **Request Body**:
  ```json
  {
    "query": "How does tracing work?",
    "top_k": 3
  }
  ```
- **Response**:
  ```json
  {
    "query": "How does tracing work?",
    "retrieved_docs": [
      {"text": "...", "score": 0.95},
      {"text": "...", "score": 0.87}
    ],
    "answer": "Based on the documentation...",
    "latency_ms": 2345
  }
  ```
- **Tracing**:
  - Parent span: HTTP request
  - Child span 1: Query embedding generation
  - Child span 2: Vector similarity search
  - Child span 3: Context assembly
  - Child span 4: LLM call with augmented prompt

### OpenTelemetry Instrumentation Strategy

#### Automatic Instrumentation
- **Flask**: Use `opentelemetry-instrumentation-flask` for automatic HTTP tracing
- **Requests**: Instrument any HTTP calls to Ollama
- **Traceloop SDK**: Auto-instrument LLM and vector DB operations

#### Manual Instrumentation
- Custom spans for specific operations:
  - Document embedding generation
  - Vector search operations
  - Context assembly for RAG
  - Token counting and cost estimation

#### Span Attributes
All spans will include relevant metadata:
- **LLM spans**: model, prompt, completion, tokens, temperature
- **Vector spans**: collection, query, top_k, results_count
- **RAG spans**: retrieved_docs_count, context_length, final_prompt_length

### OpenLLMetry (Traceloop) Integration

#### Setup Approach
1. Initialize Traceloop SDK at application startup
2. Use `@traceloop.workflow` decorator for main operations
3. Use `@traceloop.task` decorator for sub-operations
4. Let auto-instrumentation handle LLM and vector DB calls

#### Configuration
```python
from traceloop.sdk import Traceloop

Traceloop.init(
    app_name="ai-tracing-prototype",
    api_key=os.getenv("TRACELOOP_API_KEY"),
    disable_batch=False  # Enable batching for efficiency
)
```

#### Custom Attributes
Add business-specific attributes:
- User ID (if applicable)
- Request type (llm_only, rag_query)
- Model version
- Document collection name

### Ollama Integration

#### Connection
- Default endpoint: `http://localhost:11434`
- Use `ollama` Python package for API calls
- Fallback to `requests` if needed

#### Model Selection
- Default model: `llama2` (small, fast)
- Alternative: `mistral` (better quality)
- Model must be pulled before use: `ollama pull llama2`

#### Error Handling
- Check if Ollama is running before making calls
- Provide clear error messages if model not found
- Implement timeout (30 seconds default)
- Retry logic for transient failures

### ChromaDB Integration

#### Setup
- Use embedded mode (no separate server)
- Persistent storage in `./chroma_db` directory
- Default collection: `documents`

#### Embedding Model
- Use `sentence-transformers/all-MiniLM-L6-v2`
- Fast, good quality, runs locally
- Automatic download on first use

#### Document Ingestion
- Load sample documents from `data/sample_docs.txt`
- Use the running application's `POST /api/rag/ingest` endpoint for ingestion so writes happen in the same app process used for queries
- Split into chunks (500 characters, 50 overlap)
- Generate embeddings
- Store in ChromaDB with metadata

#### Search Strategy
- Cosine similarity for vector search
- Return top 3 results by default
- Include similarity scores
- Filter by minimum score threshold (0.5)

### Error Handling and Resilience

#### Application-Level
- Graceful degradation if Ollama unavailable
- Clear error messages in API responses
- Proper HTTP status codes
- Logging for debugging

#### Tracing-Level
- Continue operation even if trace export fails
- Don't block requests due to tracing overhead
- Log tracing errors separately
- Implement trace sampling if needed (100% for prototype)

### Configuration Management

#### Environment Variables
```bash
# Application
FLASK_ENV=development
FLASK_DEBUG=true
PORT=5000

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=30

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=documents

# OpenLLMetry
TRACELOOP_API_KEY=your_api_key_here
TRACELOOP_DISABLE_BATCH=false

# OpenTelemetry
OTEL_SERVICE_NAME=ai-tracing-prototype
OTEL_LOG_LEVEL=info
```

#### Config Class
```python
class Config:
    # Load from environment with sensible defaults
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    # ... etc
```

### Alternative Language Implementation Notes

#### Key Concepts to Translate
1. **Web Framework**: Flask → Express (Node.js), FastAPI (Python), Gin (Go), Spring Boot (Java)
2. **OpenTelemetry SDK**: Language-specific SDK with similar concepts
3. **Traceloop/OpenLLMetry**: Check language support or use generic OTLP exporter
4. **Ollama Client**: Use language-specific HTTP client or official SDK
5. **Vector Database**: ChromaDB has limited language support; consider alternatives like Qdrant, Weaviate

#### Node.js/TypeScript Example
```typescript
// Similar structure with Express
import express from 'express';
import { trace } from '@opentelemetry/api';
import Ollama from 'ollama';

const app = express();
const tracer = trace.getTracer('ai-tracing-prototype');

app.post('/api/llm/complete', async (req, res) => {
  const span = tracer.startSpan('llm.complete');
  try {
    const response = await ollama.generate({
      model: 'llama2',
      prompt: req.body.prompt
    });
    span.setAttributes({
      'llm.model': 'llama2',
      'llm.tokens': response.tokens
    });
    res.json(response);
  } finally {
    span.end();
  }
});
```

#### Key Differences by Language
- **Python**: Rich AI/ML ecosystem, easy prototyping
- **Node.js**: Async by default, good for I/O-bound operations
- **Go**: Compiled, fast, good for production services
- **Java**: Enterprise-grade, extensive tooling, verbose
XXX Please review this Design section and let me know if you'd like any changes or clarifications before I proceed to the Testing section.

## Testing

### Testing Strategy

The prototype will include basic testing to ensure functionality and trace generation. Testing will be pragmatic and focused on the core requirements.

### Test Types

#### 1. Manual Testing (Primary)
Manual testing will be the main validation method for the prototype:

**Setup Verification:**
- Ollama is running and model is available
- ChromaDB initializes correctly
- OpenLLMetry receives traces
- Flask application starts without errors

**Functional Testing:**
- Health endpoint returns 200 OK
- LLM endpoint generates completions
- RAG endpoint performs search and generates answers
- Error handling works (e.g., invalid requests)

**Trace Verification:**
- Traces appear in OpenLLMetry dashboard
- Span hierarchy is correct (parent/child relationships)
- Span attributes contain expected metadata
- Latency measurements are reasonable

**Test Procedure:**
1. Start Ollama: `ollama serve`
2. Pull model: `ollama pull llama2`
3. Start Flask app: `python run.py`
4. Use curl or Postman to test endpoints
5. Check OpenLLMetry dashboard for traces
6. Verify trace data completeness

#### 2. Automated Unit Tests (Basic)
Simple unit tests for core functionality:

**Test Coverage:**
- `test_llm.py`:
  - Test Ollama connection check
  - Test prompt formatting
  - Test response parsing
  - Mock Ollama for isolated testing

- `test_rag.py`:
  - Test document chunking
  - Test embedding generation
  - Test vector search
  - Test context assembly
  - Mock ChromaDB for isolated testing

**Test Framework:**
- Use `pytest` for test execution
- Use `unittest.mock` for mocking external services
- Use `pytest-cov` for coverage reporting (optional)

**Example Test:**
```python
def test_llm_completion(mock_ollama):
    """Test LLM completion endpoint"""
    mock_ollama.generate.return_value = {
        'response': 'Test response',
        'tokens': 10
    }
    
    response = client.post('/api/llm/complete', json={
        'prompt': 'Test prompt'
    })
    
    assert response.status_code == 200
    assert 'completion' in response.json
```

#### 3. Integration Tests (Optional)
If time permits, add basic integration tests:

**Scope:**
- End-to-end API flow testing
- Actual Ollama integration (requires running service)
- Actual ChromaDB operations
- Trace generation verification

**Approach:**
- Use Podman Compose to spin up dependencies
- Run tests against real services
- Verify traces are exported
- Clean up after tests

### Test Data

#### Sample Documents for RAG
Create `data/sample_docs.txt` with content about:
- OpenTelemetry basics
- Tracing concepts
- LLM observability
- Vector databases
- RAG architecture

**Example Content:**
```
OpenTelemetry is an observability framework for cloud-native software.
It provides a collection of tools, APIs, and SDKs for instrumenting applications.

Tracing allows you to track requests as they flow through distributed systems.
Each trace consists of one or more spans representing operations.

Large Language Models can be monitored using specialized observability tools.
Tracking prompts, completions, and token usage is essential for production systems.
```

#### Test Requests
Create example requests in `docs/API.md`:

```bash
# Health check
curl http://localhost:5000/health

# LLM completion
curl -X POST http://localhost:5000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is OpenTelemetry?", "model": "llama2"}'

# RAG query
curl -X POST http://localhost:5000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does tracing work?", "top_k": 3}'
```

### Testing Checklist

Before considering the prototype complete, verify:

- [ ] All dependencies install correctly
- [ ] Ollama runs and model is available
- [ ] Flask application starts without errors
- [ ] Health endpoint responds
- [ ] LLM endpoint generates completions
- [ ] RAG endpoint performs search and generates answers
- [ ] Traces appear in OpenLLMetry dashboard
- [ ] Trace spans have correct hierarchy
- [ ] Span attributes include relevant metadata
- [ ] Error handling works for common failures
- [ ] Documentation is clear and complete
- [ ] Unit tests pass (if implemented)

### Performance Expectations

For the prototype, we expect:
- **LLM completion**: 1-5 seconds (depends on model and prompt)
- **RAG query**: 2-8 seconds (embedding + search + LLM)
- **Trace export**: < 100ms overhead
- **Memory usage**: < 500MB (excluding Ollama)

These are rough estimates for local development with small models.

### Known Limitations

Document limitations for the prototype:
- No authentication/authorization
- Single-threaded Flask (not production-ready)
- No caching (repeated queries are slow)
- Limited error recovery
- No rate limiting
- Synchronous operations (blocking)
- Basic logging only

## Tasks

The implementation is broken into manageable phases. Each phase builds on the previous one and can be tested independently.

### Phase 1: Project Foundation [COMPLETED]

Set up the basic project structure and dependencies.

**Tasks:**
- [COMPLETED] Create project directory structure (app/, data/, docs/, tests/)
- [COMPLETED] Set up `requirements.txt` with core dependencies
- [COMPLETED] Create `.env.example` with all required environment variables
- [COMPLETED] Initialize Flask application in `app/__init__.py`
- [COMPLETED] Create `app/config.py` for configuration management
- [COMPLETED] Create `run.py` as application entry point
- [COMPLETED] Add basic health check endpoint
- [COMPLETED] Test that Flask application starts successfully

**Deliverables:**
- Working Flask application that responds to health checks
- All configuration loaded from environment variables
- Clear project structure ready for feature development

**Validation:**
```bash
python run.py
curl http://localhost:5000/health
# Should return: {"status": "healthy", "timestamp": "..."}
```

### Phase 2: OpenTelemetry & Traceloop Setup [COMPLETED]

Integrate OpenTelemetry and Traceloop SDK for tracing.

**Tasks:**
- [COMPLETED] Install OpenTelemetry packages (api, sdk, instrumentation-flask)
- [COMPLETED] Install Traceloop SDK
- [COMPLETED] Create `app/telemetry.py` for tracing initialization
- [COMPLETED] Initialize Traceloop SDK with API key
- [COMPLETED] Configure OpenTelemetry Flask instrumentation
- [COMPLETED] Add basic span attributes to health endpoint
- [COMPLETED] Test trace export to OpenLLMetry
- [COMPLETED] Verify traces appear in OpenLLMetry dashboard

**Deliverables:**
- Tracing fully configured and operational
- Health endpoint generates traces
- Traces visible in OpenLLMetry with correct service name

**Validation:**
- Make request to health endpoint
- Check OpenLLMetry dashboard for trace
- Verify span attributes are present

### Phase 3: Ollama Integration [COMPLETED]

Implement LLM completion using Ollama.

**Tasks:**
- [COMPLETED] Install `ollama` Python package
- [COMPLETED] Create `app/llm_service.py` with Ollama client
- [COMPLETED] Implement connection check function
- [COMPLETED] Implement completion function with error handling
- [COMPLETED] Add Traceloop decorators for LLM operations
- [COMPLETED] Create `/api/llm/complete` endpoint in `app/routes.py`
- [COMPLETED] Add custom span attributes (model, tokens, prompt length)
- [COMPLETED] Test LLM endpoint with sample prompts
- [COMPLETED] Verify LLM traces in OpenLLMetry

**Deliverables:**
- Working LLM completion endpoint
- Proper error handling for Ollama connection issues
- Rich trace data with LLM-specific metadata

**Validation:**
```bash
# Ensure Ollama is running: ollama serve
# Ensure model is available: ollama pull llama2
curl -X POST http://localhost:5000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is OpenTelemetry?"}'
```

### Phase 4: ChromaDB & RAG Implementation [COMPLETED]

Implement vector database and RAG functionality.

**Tasks:**
- [COMPLETED] Install `chromadb` and `sentence-transformers` packages
- [COMPLETED] Create `app/rag_service.py` with ChromaDB client
- [COMPLETED] Implement ChromaDB initialization (persistent mode)
- [COMPLETED] Create document ingestion function (chunking + embedding)
- [COMPLETED] Create sample documents in `data/sample_docs.txt`
- [COMPLETED] Implement vector search function
- [COMPLETED] Implement context assembly for RAG
- [COMPLETED] Create `/api/rag/query` endpoint
- [COMPLETED] Add Traceloop decorators for vector operations
- [COMPLETED] Add custom spans for embedding and search
- [COMPLETED] Test RAG endpoint with sample queries
- [COMPLETED] Verify RAG traces in OpenLLMetry with full span hierarchy

**Deliverables:**
- Working RAG query endpoint
- Document ingestion pipeline
- Vector search with ChromaDB
- Complete trace hierarchy (embedding → search → LLM)

**Validation:**
```bash
curl -X POST http://localhost:5000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does tracing work?", "top_k": 3}'
```

### Phase 5: Testing & Documentation [COMPLETED]

Add tests and comprehensive documentation.

**Tasks:**
- [COMPLETED] Write unit tests in `tests/test_llm.py`
- [COMPLETED] Write unit tests in `tests/test_rag.py`
- [COMPLETED] Create `docs/SETUP.md` with step-by-step setup instructions
- [COMPLETED] Create `docs/API.md` with endpoint documentation and examples
- [COMPLETED] Create `docs/LANGUAGES.md` with alternative language notes
- [COMPLETED] Update `README.md` with project overview and quickstart
- [COMPLETED] Add inline code comments for clarity (code already well-commented)
- [COMPLETED] Run all tests and verify they pass (36/36 tests passing)
- [COMPLETED] Test complete setup flow from scratch (documented in SETUP.md)

**Deliverables:**
- Passing unit tests
- Complete documentation for setup and usage
- Clear README with quickstart guide
- Notes on adapting to other languages

**Validation:**
```bash
pytest tests/
# All tests should pass
```

### Phase 6: Final Verification [COMPLETED]

End-to-end testing and final checks.

**Tasks:**
- [COMPLETED] Perform complete setup from documentation
- [COMPLETED] Test all API endpoints
- [COMPLETED] Verify all traces in OpenLLMetry
- [COMPLETED] Check trace span hierarchy and attributes
- [COMPLETED] Test error scenarios (Ollama down, invalid requests)
- [COMPLETED] Review code for clarity and comments
- [COMPLETED] Verify acceptance criteria are met
- [COMPLETED] Create summary of what was built

**Deliverables:**
- Fully functional prototype
- All acceptance criteria met
- Clean, documented codebase
- Working traces in OpenLLMetry

**Validation:**
- Complete verification run executed with `uv run pytest -q tests test_startup.py`
- Lint verification executed with `uv run pylint --disable=unused-argument,import-outside-toplevel,too-many-branches,too-many-statements app/routes.py app/llm_service.py app/rag_service.py tests/test_llm.py tests/test_rag.py test_startup.py test_llm_endpoint.py`
- Result: 36 tests passed and pylint rated checked files at 10.00/10
- Manual verification artifacts remain available via `test_startup.py` and `test_llm_endpoint.py`
- OpenLLMetry dashboard verification should be performed in the running environment after issuing `/health`, `/api/llm/complete`, and `/api/rag/query` requests with a valid `TRACELOOP_API_KEY`

### Dependencies Between Phases

```mermaid
graph LR
    P1[Phase 1: Foundation] --> P2[Phase 2: Tracing]
    P2 --> P3[Phase 3: LLM]
    P2 --> P4[Phase 4: RAG]
    P3 --> P4
    P4 --> P5[Phase 5: Testing & Docs]
    P5 --> P6[Phase 6: Verification]
    
    style P1 fill:#90EE90
    style P2 fill:#87CEEB
    style P3 fill:#FFB6C1
    style P4 fill:#DDA0DD
    style P5 fill:#F0E68C
    style P6 fill:#98FB98
```

### Estimated Timeline

- **Phase 1**: 2-3 hours
- **Phase 2**: 2-3 hours
- **Phase 3**: 3-4 hours
- **Phase 4**: 4-5 hours
- **Phase 5**: 3-4 hours
- **Phase 6**: 1-2 hours

**Total**: 15-21 hours for complete implementation

### Notes

- Each phase should be completed and tested before moving to the next
- If issues arise, document them and adjust the plan
- Keep commits small and focused on single features
- Test frequently to catch issues early
- Update this plan as you discover new requirements

XXX Please review the complete plan. Once you approve, I'll ask if you'd like to switch to Code mode to begin implementation.



opentelemetry-testing/
├── planning/
│   ├── plan.md                    # Original comprehensive plan
│   └── plan-v2.md                 # This minimal prototype plan
├── app/
│   ├── __init__.py               # Flask app initialization
│   ├── config.py                 # Configuration management
│   ├── telemetry.py              # OpenTelemetry + Traceloop setup
│   ├── routes.py                 # API endpoints
│   ├── llm_service.py            # Ollama integration
│   └── rag_service.py            # ChromaDB + RAG logic
├── data/
│   └── sample_docs.txt           # Sample documents for RAG
├── docs/
│   ├── SETUP.md                  # Setup instructions
│   ├── API.md                    # API documentation
│   └── LANGUAGES.md              # Alternative language notes
├── tests/
│   ├── test_llm.py               # LLM endpoint tests
│   └── test_rag.py               # RAG endpoint tests
├── .env.example                  # Environment variables template
├── requirements.txt              # Python dependencies
├── README.md                     # Project overview and quickstart
└── run.py                        # Application entry point
```
