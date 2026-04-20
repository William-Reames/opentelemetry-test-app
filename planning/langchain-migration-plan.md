# LangChain Migration Plan

## Overview

Migrate from direct Ollama client calls to using LangChain's ChatOllama. This will provide better integration with the LangChain ecosystem while maintaining tracing capabilities.

## Acceptance Criteria

- [ ] All LLM calls use ChatOllama instead of direct ollama.Client
- [ ] Tracing still works correctly for LLM and RAG operations
- [ ] All existing tests pass with updated mocks
- [ ] No breaking changes to API endpoints
- [ ] Code is cleaner and follows LangChain best practices

## Design

### Current Architecture

The current implementation uses:
- `ollama.Client` for direct API calls
- Custom response normalization (`_normalize_generate_response`)
- Manual token counting from Ollama responses
- Traceloop decorators (`@task`, `@workflow`) for tracing

### Target Architecture

The new implementation will use:
- `ChatOllama` from `langchain_ollama` package
- LangChain's standard message format (HumanMessage, AIMessage)
- LangChain's built-in response handling
- Traceloop decorators maintained for tracing
- LangChain's callback system for additional telemetry if needed

### Key Changes

#### 1. Import Changes in app/llm_service.py

**Remove:**
```python
import ollama
```

**Add:**
```python
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
```

#### 2. ChatOllama Initialization

Replace `ollama.Client(host=Config.OLLAMA_HOST)` with:
```python
ChatOllama(
    base_url=Config.OLLAMA_HOST,
    model=selected_model,
    temperature=temperature,
    num_predict=max_tokens  # if provided
)
```

#### 3. Response Handling

LangChain returns `AIMessage` objects with:
- `content`: The generated text
- `response_metadata`: Contains token counts and other metadata

Token counting will need to be extracted from `response_metadata` instead of direct Ollama response fields.

#### 4. Connection Checking

The `check_ollama_connection()` function will need to:
- Create a ChatOllama instance
- Attempt a simple call or use a different method to verify connectivity
- May need to keep some direct ollama client usage for listing models

#### 5. Error Handling

Replace `ollama.ResponseError` with LangChain exceptions:
- Import from `langchain_core.exceptions`
- Handle `LangChainException` or more specific exceptions

### Tracing Considerations

- Traceloop SDK should automatically instrument LangChain calls
- Keep existing `@task` and `@workflow` decorators
- Manual span attributes should still work
- May get additional automatic attributes from LangChain instrumentation

### Files to Modify

1. **app/llm_service.py** (Primary changes)
   - Replace ollama client with ChatOllama
   - Update `check_ollama_connection()`
   - Update `generate_completion()`
   - Update `complete_with_ollama()`
   - Remove helper functions that are no longer needed

2. **app/rag_service.py** (Minor changes)
   - Import changes if needed
   - Verify compatibility with new LLM service

3. **tests/test_llm.py** (Test updates)
   - Mock ChatOllama instead of ollama.Client
   - Update response structures to match LangChain format
   - Adjust assertions for new response format

4. **tests/test_rag.py** (Verification)
   - Ensure RAG tests still pass
   - Update mocks if needed

## Testing

### Unit Tests

- [ ] All tests in `tests/test_llm.py` pass
- [ ] All tests in `tests/test_rag.py` pass
- [ ] Test coverage remains high

### Integration Tests

- [ ] Manual test of `/api/llm/complete` endpoint
- [ ] Manual test of `/api/rag/query` endpoint
- [ ] Verify traces appear in Traceloop dashboard

### Tracing Verification

- [ ] LLM calls generate traces
- [ ] RAG workflows generate traces
- [ ] Token counts are captured
- [ ] Latency metrics are captured
- [ ] Error traces work correctly

## Tasks

### Phase 1: Core Migration

- [ ] Update imports in `app/llm_service.py`
- [ ] Rewrite `generate_completion()` to use ChatOllama
- [ ] Update `check_ollama_connection()` for compatibility
- [ ] Update `complete_with_ollama()` workflow
- [ ] Remove obsolete helper functions (`_normalize_generate_response`, etc.)

### Phase 2: Test Updates

- [ ] Update test mocks in `tests/test_llm.py`
- [ ] Fix test assertions for new response format
- [ ] Run tests and fix any failures
- [ ] Update `tests/test_rag.py` if needed

### Phase 3: Verification

- [ ] Run full test suite with `uv run pytest`
- [ ] Start the application and test endpoints manually
- [ ] Verify traces in Traceloop dashboard
- [ ] Check that token counts and metrics are correct

### Phase 4: Cleanup

- [ ] Remove unused imports
- [ ] Run `uv run pylint` to check code quality
- [ ] Update any documentation if needed
- [ ] Verify no breaking changes to API

## Implementation Notes

### Token Counting

LangChain's ChatOllama response includes token information in `response_metadata`:
```python
response.response_metadata = {
    'model': 'llama2',
    'created_at': '...',
    'done': True,
    'total_duration': ...,
    'prompt_eval_count': 10,  # prompt tokens
    'eval_count': 15,  # completion tokens
    ...
}
```

### Model Availability Check

For checking available models, we may need to keep a small amount of direct ollama client usage:
```python
import ollama
client = ollama.Client(host=Config.OLLAMA_HOST)
models = client.list()
```

This is acceptable as it's only for the connection check, not for LLM calls.

### Streaming Support

If streaming is needed in the future, ChatOllama supports it via:
```python
for chunk in llm.stream([HumanMessage(content=prompt)]):
    print(chunk.content, end="", flush=True)
```

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Token counts not available in LangChain response | Check response_metadata structure; fallback to estimation if needed |
| Tracing doesn't work with LangChain | Traceloop SDK should auto-instrument; verify early in testing |
| Breaking changes to API responses | Keep response structure similar; map LangChain responses to expected format |
| Model availability checking breaks | Keep minimal ollama client usage for connection checks |

## Rollback Plan

If issues arise:
1. Revert changes to `app/llm_service.py`
2. Revert test changes
3. The ollama package is still in dependencies, so rollback is straightforward

## Success Criteria

✅ All tests pass
✅ API endpoints work correctly
✅ Traces appear in Traceloop dashboard
✅ Token counts are accurate
✅ No performance degradation
✅ Code is cleaner and more maintainable