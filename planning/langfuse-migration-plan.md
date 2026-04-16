# Implementation Plan: Add LangFuse Support (Multi-Backend Architecture)

## Overview

This plan outlines adding self-hosted LangFuse as an **alternative tracing backend** alongside the existing TraceLoop integration. Users will be able to choose which platform to use via configuration, or even use both simultaneously.

## Acceptance Criteria

✅ Keep OpenTelemetry as the core instrumentation layer
✅ Support **both** TraceLoop and LangFuse as configurable backends
✅ Allow users to choose backend via environment variable
✅ Maintain all current tracing capabilities (LLM calls, RAG queries, HTTP requests)
✅ Provide Podman Compose setup for LangFuse
✅ Update documentation to explain both options
✅ Ensure backward compatibility with existing TraceLoop setup

## Current State Analysis

### Current Architecture
```
Flask App → OpenTelemetry SDK → Traceloop SDK → TraceLoop Cloud
                ↓
         Traceloop Decorators
         (@workflow, @task)
```

### Current Dependencies
- `traceloop-sdk>=0.20.0` - Provides decorators and TraceLoop integration
- `opentelemetry-api>=1.22.0` - Core OpenTelemetry API
- `opentelemetry-sdk>=1.22.0` - OpenTelemetry SDK
- `opentelemetry-instrumentation-flask>=0.43b0` - Flask auto-instrumentation

### Current Traceloop Usage
1. **[`app/telemetry.py`](app/telemetry.py:13)** - `Traceloop.init()` initialization
2. **[`app/llm_service.py`](app/llm_service.py:15)** - `@workflow` and `@task` decorators
3. **[`app/rag_service.py`](app/rag_service.py)** - Similar decorator usage (needs verification)
4. **[`app/config.py`](app/config.py:32-33)** - `TRACELOOP_API_KEY` and `TRACELOOP_DISABLE_BATCH` config

## Target Architecture

### New Multi-Backend Architecture
```
                    ┌─────────────────────────┐
                    │     Flask App           │
                    │  (OpenTelemetry SDK)    │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
         ┌──────────▼─────────┐  ┌─────────▼──────────┐
         │  Traceloop SDK     │  │ LangFuse Processor │
         │  (if enabled)      │  │  (if enabled)      │
         └──────────┬─────────┘  └─────────┬──────────┘
                    │                      │
         ┌──────────▼─────────┐  ┌─────────▼──────────┐
         │  TraceLoop Cloud   │  │ LangFuse (Self-    │
         │                    │  │  Hosted)           │
         └────────────────────┘  └────────────────────┘
```

### Key Design Principles
1. **Keep**: Traceloop SDK and decorators (backward compatible)
2. **Add**: LangFuse span processor as optional backend
3. **Add**: Configuration to choose backend(s)
4. **Support**: Using both backends simultaneously
5. **Maintain**: Existing decorator-based tracing (works with both)

## Design

### 1. Backend Selection Strategy

Users can configure which backend(s) to use via environment variable:

```bash
# Option 1: TraceLoop only (current default)
TRACING_BACKEND=traceloop
TRACELOOP_API_KEY=your_key

# Option 2: LangFuse only
TRACING_BACKEND=langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# Option 3: Both backends (dual export)
TRACING_BACKEND=traceloop,langfuse
TRACELOOP_API_KEY=your_key
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# Option 4: Disabled (no tracing)
TRACING_BACKEND=none
```

### 2. LangFuse Integration Approach

**Use LangFuse's OpenTelemetry Span Processor** alongside Traceloop:

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from traceloop.sdk import Traceloop
from langfuse.opentelemetry import LangfuseSpanProcessor

def initialize_telemetry(app, config):
    """Initialize tracing with configurable backends."""
    backends = config.TRACING_BACKEND.split(',')
    
    # Initialize TraceLoop if enabled
    if 'traceloop' in backends and config.TRACELOOP_API_KEY:
        Traceloop.init(
            app_name=config.OTEL_SERVICE_NAME,
            api_key=config.TRACELOOP_API_KEY,
            disable_batch=config.TRACELOOP_DISABLE_BATCH,
        )
    
    # Add LangFuse processor if enabled
    if 'langfuse' in backends and config.LANGFUSE_PUBLIC_KEY:
        tracer_provider = trace.get_tracer_provider()
        langfuse_processor = LangfuseSpanProcessor(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            host=config.LANGFUSE_HOST,
        )
        tracer_provider.add_span_processor(langfuse_processor)
    
    # Flask instrumentation (works with both)
    FlaskInstrumentor().instrument_app(app)
```

**Benefits of This Approach:**
- ✅ Keeps existing Traceloop decorators working
- ✅ No breaking changes to existing code
- ✅ Both backends receive the same spans
- ✅ Easy to switch or use both
- ✅ Minimal code changes required

### 3. LangFuse Deployment Options

#### Option A: Podman Compose (Recommended for Development)
```yaml
# compose.yml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse
    volumes:
      - langfuse_db:/var/lib/postgresql/data
    
  langfuse:
    image: langfuse/langfuse:latest
    depends_on:
      - postgres
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@postgres:5432/langfuse
      NEXTAUTH_SECRET: changeme
      NEXTAUTH_URL: http://localhost:3000
      SALT: changeme

volumes:
  langfuse_db:
```

#### Option B: Manual Setup
- Install LangFuse from source or binary
- Configure PostgreSQL separately
- More control but more complex setup

### 4. Configuration Changes

**New Environment Variables (Additive):**
```bash
# Backend Selection
TRACING_BACKEND=traceloop  # Options: traceloop, langfuse, traceloop,langfuse, none

# LangFuse Configuration (optional, only if using langfuse backend)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# Existing TraceLoop Configuration (keep as-is)
TRACELOOP_API_KEY=...
TRACELOOP_DISABLE_BATCH=false
```

### 5. Decorator Compatibility

**No changes needed!** Traceloop decorators work with both backends:

```python
from traceloop.sdk.decorators import task, workflow

@task(name="generate_completion")
def generate_completion(prompt: str) -> Dict[str, Any]:
    # This function's spans will be sent to:
    # - TraceLoop (if enabled)
    # - LangFuse (if enabled)
    # - Both (if both enabled)
    pass
```

The decorators create OpenTelemetry spans, which are then processed by whichever span processors are configured.

### 6. Span Attribute Compatibility

Both backends use OpenTelemetry semantic conventions, so existing attributes work:

| Attribute | TraceLoop | LangFuse | Notes |
|-----------|-----------|----------|-------|
| `llm.model` | ✅ | ✅ | Both support |
| `llm.prompt_tokens` | ✅ | ✅ | Token counting |
| `llm.completion_tokens` | ✅ | ✅ | Token counting |
| `llm.total_tokens` | ✅ | ✅ | Total usage |
| `llm.temperature` | ✅ | ✅ | Model parameters |

**Optional Enhancement**: Add LangFuse-specific attributes when LangFuse is enabled:
```python
if 'langfuse' in config.TRACING_BACKEND:
    span.set_attribute("gen_ai.request.model", model)
    span.set_attribute("gen_ai.usage.prompt_tokens", prompt_tokens)
```

## Testing Strategy

### Unit Tests
- Test backend selection logic
- Test initialization with different backend configurations
- Test that decorators work with both backends
- Test graceful degradation when backends are unavailable

### Integration Tests
- Verify traces appear in TraceLoop (when enabled)
- Verify traces appear in LangFuse (when enabled)
- Verify traces appear in both (when both enabled)
- Check span hierarchy is preserved in both
- Validate all attributes are captured

### Manual Testing Checklist
- [ ] TraceLoop-only mode works (existing behavior)
- [ ] LangFuse-only mode works
- [ ] Dual-backend mode works (both receive traces)
- [ ] Disabled mode works (no tracing overhead)
- [ ] LangFuse instance starts successfully
- [ ] Application connects to LangFuse
- [ ] LLM completion traces appear in selected backend(s)
- [ ] RAG query traces appear with proper hierarchy
- [ ] HTTP request traces are captured
- [ ] Error traces include proper error information

## Tasks

### Phase 1: Infrastructure Setup
- [x] Create `compose.yml` for LangFuse stack (PostgreSQL + LangFuse)
- [x] Create `compose-v2.yml` for simpler PostgreSQL-only setup
- [x] Create `docs/LANGFUSE_SETUP.md` with deployment instructions
- [x] Test LangFuse deployment with Podman Compose
- [x] Document manual setup process
- [x] Verify LangFuse UI is accessible
- [x] Create API keys in LangFuse UI (documented in setup guide)

### Phase 2: Dependency Updates
- [x] Add `langfuse` SDK to [`pyproject.toml`](pyproject.toml) (keep traceloop-sdk)
- [x] Run `uv sync` to update dependencies
- [x] Verify no dependency conflicts
- [x] Run `uv run pylint app/` to check for issues

### Phase 3: Code Updates

#### 3.1 Update [`app/config.py`](app/config.py)
- [x] Add `TRACING_BACKEND` configuration (default: "traceloop")
- [x] Add `LANGFUSE_PUBLIC_KEY` (optional)
- [x] Add `LANGFUSE_SECRET_KEY` (optional)
- [x] Add `LANGFUSE_HOST` (default: "http://localhost:3000")
- [x] Keep existing TraceLoop configuration
- [x] Update `validate()` method to check backend-specific requirements
- [x] Update `display()` method to show backend selection

#### 3.2 Update [`app/telemetry.py`](app/telemetry.py)
- [x] Add LangFuse imports (conditional)
- [x] Add backend selection logic
- [x] Initialize TraceLoop if `'traceloop'` in backends
- [x] Add LangFuse span processor if `'langfuse'` in backends
- [x] Support both backends simultaneously
- [x] Add error handling for each backend
- [x] Keep existing `add_span_attributes()` helper
- [x] Add logging for which backends are active

#### 3.3 Update [`app/llm_service.py`](app/llm_service.py)
- [x] **No changes required** - decorators work with both backends
- [x] Optional: Add LangFuse-specific attributes when enabled
- [x] Verify existing span attributes work with both

#### 3.4 Update [`app/rag_service.py`](app/rag_service.py)
- [x] **No changes required** - decorators work with both backends
- [x] Optional: Add LangFuse-specific attributes when enabled

#### 3.5 Update [`.env.example`](.env.example)
- [x] Add `TRACING_BACKEND` with examples
- [x] Add LangFuse configuration section
- [x] Keep existing TraceLoop configuration
- [x] Add comments explaining backend options
- [x] Include example keys format

### Phase 4: Testing Updates

#### 4.1 Update [`tests/test_telemetry.py`](tests/test_telemetry.py)
- [ ] Add tests for backend selection logic
- [ ] Test TraceLoop-only initialization
- [ ] Test LangFuse-only initialization
- [ ] Test dual-backend initialization
- [ ] Test disabled mode
- [ ] Test graceful degradation when backends unavailable
- [ ] Verify existing tests still pass

#### 4.2 Update [`tests/test_llm.py`](tests/test_llm.py)
- [ ] Verify tests work with different backend configurations
- [ ] Add tests for backend-specific attributes (optional)
- [ ] Ensure no breaking changes

#### 4.3 Update [`tests/test_rag.py`](tests/test_rag.py)
- [ ] Verify tests work with different backend configurations
- [ ] Ensure RAG span hierarchy works with both backends

### Phase 5: Documentation Updates

#### 5.1 Update [`README.md`](README.md)
- [ ] Update architecture diagram to show multi-backend support
- [ ] Add LangFuse as an alternative to TraceLoop
- [ ] Update prerequisites section (LangFuse optional)
- [ ] Add backend selection instructions
- [ ] Update "View Traces" section for both platforms
- [ ] Update technology stack table
- [ ] Add comparison: TraceLoop vs LangFuse
- [ ] Update troubleshooting for both backends

#### 5.2 Update [`docs/SETUP.md`](docs/SETUP.md)
- [ ] Add section on choosing a tracing backend
- [ ] Add LangFuse deployment instructions
- [ ] Update environment variable configuration
- [ ] Add backend-specific setup steps
- [ ] Update troubleshooting guide

#### 5.3 Create `docs/LANGFUSE_SETUP.md`
- [ ] Document Podman Compose setup
- [ ] Document manual PostgreSQL setup
- [ ] Document LangFuse configuration
- [ ] Add screenshots of LangFuse UI
- [ ] Include API key generation steps
- [ ] Add troubleshooting tips
- [ ] Compare with TraceLoop setup

#### 5.4 Create `docs/TRACING_BACKENDS.md`
- [ ] Document backend selection options
- [ ] Compare TraceLoop vs LangFuse features
- [ ] Explain when to use each backend
- [ ] Document dual-backend use cases
- [ ] Include performance considerations

#### 5.5 Update [`docs/API.md`](docs/API.md)
- [ ] Note that tracing works with both backends
- [ ] Update any backend-specific examples

### Phase 6: Verification & Cleanup
- [ ] Run full test suite: `uv run pytest tests/ -v`
- [ ] Run with coverage: `uv run pytest tests/ --cov=app`
- [ ] Run pylint: `uv run pylint app/`
- [ ] Test TraceLoop-only mode manually
- [ ] Test LangFuse-only mode manually
- [ ] Test dual-backend mode manually
- [ ] Verify traces in TraceLoop UI
- [ ] Verify traces in LangFuse UI
- [ ] Check span hierarchy in both
- [ ] Verify backward compatibility
- [ ] Update [`planning/plan.md`](planning/plan.md) if needed

## Implementation Risks & Mitigations

### Risk 1: Dependency Conflicts
**Risk**: LangFuse SDK might conflict with Traceloop SDK
**Mitigation**: Test thoroughly; both use OpenTelemetry, so conflicts unlikely

### Risk 2: Performance Overhead
**Risk**: Dual-backend mode might have higher overhead
**Mitigation**: Use batch span processors; benchmark performance; document overhead

### Risk 3: Configuration Complexity
**Risk**: More configuration options might confuse users
**Mitigation**: Provide clear documentation; sensible defaults; validation

### Risk 4: LangFuse Deployment Issues
**Risk**: Self-hosted LangFuse might be complex to set up
**Mitigation**: Provide Podman Compose file; comprehensive documentation

### Risk 5: Backward Compatibility
**Risk**: Changes might break existing TraceLoop setup
**Mitigation**: Default to TraceLoop-only mode; extensive testing; no breaking changes

## Rollback Plan

If implementation fails:
1. Revert code changes via git
2. Remove `langfuse` dependency (keep traceloop-sdk)
3. Restore original configuration
4. Run `uv sync` to restore dependencies
5. Restart application

**Note**: Since we're adding features, not replacing, rollback is simple.

## Success Metrics

- [ ] All tests pass
- [ ] Backward compatibility maintained (TraceLoop works as before)
- [ ] LangFuse-only mode works
- [ ] Dual-backend mode works
- [ ] Traces visible in selected backend(s)
- [ ] Span hierarchy preserved in both backends
- [ ] All attributes captured correctly
- [ ] Documentation complete and accurate
- [ ] Performance within acceptable range (< 15% overhead for dual mode)

## Timeline Estimate

- **Phase 1** (Infrastructure): 2-3 hours
- **Phase 2** (Dependencies): 30 minutes
- **Phase 3** (Code Updates): 3-4 hours (less than migration!)
- **Phase 4** (Testing): 2-3 hours
- **Phase 5** (Documentation): 3-4 hours
- **Phase 6** (Verification): 1-2 hours

**Total Estimated Time**: 12-17 hours

## Backend Comparison

### TraceLoop (OpenLLMetry)
**Pros:**
- ✅ Cloud-hosted (no infrastructure needed)
- ✅ Quick setup (just API key)
- ✅ Managed service
- ✅ Built-in AI-specific features

**Cons:**
- ❌ Requires internet connection
- ❌ Data sent to third-party
- ❌ Subscription costs
- ❌ Less control over data

### LangFuse (Self-Hosted)
**Pros:**
- ✅ Full data control
- ✅ No subscription costs
- ✅ Works offline
- ✅ Customizable
- ✅ Open source

**Cons:**
- ❌ Requires infrastructure setup
- ❌ Need to manage PostgreSQL
- ❌ More complex deployment
- ❌ Self-maintenance required

### Dual-Backend Mode
**Use Cases:**
- Migration period (testing LangFuse while keeping TraceLoop)
- Redundancy (backup tracing)
- Comparison (evaluate both platforms)
- Hybrid (dev uses LangFuse, prod uses TraceLoop)

## References

- [LangFuse Documentation](https://langfuse.com/docs)
- [LangFuse OpenTelemetry Integration](https://langfuse.com/docs/integrations/opentelemetry)
- [LangFuse Self-Hosting Guide](https://langfuse.com/docs/deployment/self-host)
- [TraceLoop Documentation](https://www.traceloop.com/docs)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Semantic Conventions for GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)

---
