# Alternative Language Implementation Guide

This guide provides notes and considerations for implementing the OpenTelemetry AI tracing prototype in programming languages other than Python.

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Language-Specific Implementations](#language-specific-implementations)
  - [Node.js/TypeScript](#nodejstypescript)
  - [Go](#go)
  - [Java](#java)
  - [C#/.NET](#cnet)
- [Component Alternatives](#component-alternatives)
- [Common Challenges](#common-challenges)

## Overview

The Python implementation uses:
- **Flask** for the web framework
- **Ollama Python SDK** for LLM integration
- **ChromaDB** for vector storage
- **OpenTelemetry Python SDK** for tracing
- **Traceloop SDK** for enhanced AI observability

When adapting to other languages, you'll need to find equivalent libraries and understand how to integrate them.

## Core Concepts

These concepts are language-agnostic and should be preserved in any implementation:

### 1. OpenTelemetry Tracing

**Key Concepts:**
- **Spans**: Represent individual operations
- **Traces**: Collections of related spans
- **Context Propagation**: Passing trace context between operations
- **Attributes**: Metadata attached to spans

**Implementation Pattern:**
```
1. Initialize OpenTelemetry SDK
2. Configure trace exporter (OTLP to OpenLLMetry)
3. Create spans for operations
4. Add relevant attributes
5. Ensure proper span lifecycle (start/end)
```

### 2. LLM Integration

**Key Concepts:**
- HTTP client to communicate with Ollama
- Request/response handling
- Error handling for connection issues
- Token counting and metadata extraction

**Implementation Pattern:**
```
1. Check if Ollama is available
2. Verify model is pulled
3. Send generation request
4. Parse response
5. Extract metadata (tokens, latency)
6. Add trace attributes
```

### 3. Vector Database (RAG)

**Key Concepts:**
- Document chunking with overlap
- Embedding generation
- Similarity search
- Context assembly for LLM

**Implementation Pattern:**
```
1. Chunk documents intelligently
2. Generate embeddings (or use DB's built-in)
3. Store with metadata
4. Query with similarity search
5. Assemble context from results
6. Generate answer with LLM
```

## Language-Specific Implementations

### Node.js/TypeScript

#### Recommended Stack

```typescript
// Web Framework
import express from 'express';

// OpenTelemetry
import { trace } from '@opentelemetry/api';
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

// Ollama Client
import Ollama from 'ollama';

// Vector Database (alternatives)
import { ChromaClient } from 'chromadb';
// OR
import { QdrantClient } from '@qdrant/js-client-rest';
```

#### Example: LLM Completion Endpoint

```typescript
import express from 'express';
import { trace } from '@opentelemetry/api';
import Ollama from 'ollama';

const app = express();
const tracer = trace.getTracer('ai-tracing-prototype');
const ollama = new Ollama({ host: 'http://localhost:11434' });

app.post('/api/llm/complete', async (req, res) => {
  const span = tracer.startSpan('llm.complete');
  
  try {
    const { prompt, model = 'llama2', max_tokens } = req.body;
    
    // Add span attributes
    span.setAttributes({
      'llm.model': model,
      'llm.prompt_length': prompt.length,
    });
    
    const startTime = Date.now();
    
    // Call Ollama
    const response = await ollama.generate({
      model,
      prompt,
      options: {
        num_predict: max_tokens,
      },
    });
    
    const latency = Date.now() - startTime;
    
    // Add more attributes
    span.setAttributes({
      'llm.completion_length': response.response.length,
      'llm.latency_ms': latency,
    });
    
    res.json({
      completion: response.response,
      model,
      latency_ms: latency,
    });
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: 2 }); // ERROR
    res.status(500).json({ error: error.message });
  } finally {
    span.end();
  }
});
```

#### Key Differences from Python

- **Async/Await**: Node.js is async by default, use `async/await` everywhere
- **Type Safety**: TypeScript provides compile-time type checking
- **Error Handling**: Use try/catch with proper error types
- **Package Management**: Use npm/yarn/pnpm instead of pip/uv

#### Challenges

- ChromaDB has limited Node.js support (consider Qdrant or Weaviate)
- Traceloop SDK may not be available (use OpenTelemetry directly)
- Need to handle async operations carefully

---

### Go

#### Recommended Stack

```go
// Web Framework
import "github.com/gin-gonic/gin"

// OpenTelemetry
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
)

// HTTP Client for Ollama
import "net/http"

// Vector Database
// Use Qdrant or Weaviate (better Go support)
```

#### Example: LLM Completion Endpoint

```go
package main

import (
    "context"
    "encoding/json"
    "net/http"
    "time"
    
    "github.com/gin-gonic/gin"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
)

type CompletionRequest struct {
    Prompt    string  `json:"prompt" binding:"required"`
    Model     string  `json:"model"`
    MaxTokens int     `json:"max_tokens,omitempty"`
}

type CompletionResponse struct {
    Completion string `json:"completion"`
    Model      string `json:"model"`
    LatencyMs  int64  `json:"latency_ms"`
}

func completionHandler(c *gin.Context) {
    tracer := otel.Tracer("ai-tracing-prototype")
    ctx, span := tracer.Start(c.Request.Context(), "llm.complete")
    defer span.End()
    
    var req CompletionRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    
    if req.Model == "" {
        req.Model = "llama2"
    }
    
    // Add span attributes
    span.SetAttributes(
        attribute.String("llm.model", req.Model),
        attribute.Int("llm.prompt_length", len(req.Prompt)),
    )
    
    startTime := time.Now()
    
    // Call Ollama (implement ollamaGenerate function)
    completion, err := ollamaGenerate(ctx, req.Prompt, req.Model, req.MaxTokens)
    if err != nil {
        span.RecordError(err)
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    
    latency := time.Since(startTime).Milliseconds()
    
    span.SetAttributes(
        attribute.Int("llm.completion_length", len(completion)),
        attribute.Int64("llm.latency_ms", latency),
    )
    
    c.JSON(http.StatusOK, CompletionResponse{
        Completion: completion,
        Model:      req.Model,
        LatencyMs:  latency,
    })
}
```

#### Key Differences from Python

- **Static Typing**: Go is statically typed, define structs for requests/responses
- **Error Handling**: Explicit error returns, no exceptions
- **Concurrency**: Use goroutines and channels for concurrent operations
- **Performance**: Compiled language, generally faster than Python

#### Challenges

- More verbose than Python
- Limited AI/ML library ecosystem
- Need to implement more functionality manually
- ChromaDB has no official Go client

---

### Java

#### Recommended Stack

```java
// Web Framework
import org.springframework.boot.SpringApplication;
import org.springframework.web.bind.annotation.*;

// OpenTelemetry
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.sdk.OpenTelemetrySdk;

// HTTP Client
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

// Vector Database
// Use Qdrant, Weaviate, or Pinecone
```

#### Example: LLM Completion Endpoint

```java
import org.springframework.web.bind.annotation.*;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.common.AttributeKey;

@RestController
@RequestMapping("/api/llm")
public class LLMController {
    
    private final Tracer tracer;
    private final OllamaService ollamaService;
    
    public LLMController(Tracer tracer, OllamaService ollamaService) {
        this.tracer = tracer;
        this.ollamaService = ollamaService;
    }
    
    @PostMapping("/complete")
    public CompletionResponse complete(@RequestBody CompletionRequest request) {
        Span span = tracer.spanBuilder("llm.complete").startSpan();
        
        try {
            String model = request.getModel() != null ? request.getModel() : "llama2";
            
            // Add span attributes
            span.setAttribute("llm.model", model);
            span.setAttribute("llm.prompt_length", request.getPrompt().length());
            
            long startTime = System.currentTimeMillis();
            
            // Call Ollama
            String completion = ollamaService.generate(
                request.getPrompt(),
                model,
                request.getMaxTokens()
            );
            
            long latency = System.currentTimeMillis() - startTime;
            
            span.setAttribute("llm.completion_length", completion.length());
            span.setAttribute("llm.latency_ms", latency);
            
            return new CompletionResponse(completion, model, latency);
            
        } catch (Exception e) {
            span.recordException(e);
            throw new RuntimeException("Completion failed", e);
        } finally {
            span.end();
        }
    }
}
```

#### Key Differences from Python

- **Spring Boot**: Enterprise-grade framework with dependency injection
- **Strong Typing**: Compile-time type safety
- **Annotations**: Heavy use of annotations for configuration
- **Verbosity**: More boilerplate code than Python

#### Challenges

- More complex setup and configuration
- Steeper learning curve
- Heavier resource usage
- Limited AI/ML libraries compared to Python

---

### C#/.NET

#### Recommended Stack

```csharp
// Web Framework
using Microsoft.AspNetCore.Mvc;

// OpenTelemetry
using OpenTelemetry;
using OpenTelemetry.Trace;
using System.Diagnostics;

// HTTP Client
using System.Net.Http;

// Vector Database
// Use Qdrant, Weaviate, or Azure Cognitive Search
```

#### Example: LLM Completion Endpoint

```csharp
using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;

[ApiController]
[Route("api/llm")]
public class LLMController : ControllerBase
{
    private readonly ActivitySource _activitySource;
    private readonly IOllamaService _ollamaService;
    
    public LLMController(ActivitySource activitySource, IOllamaService ollamaService)
    {
        _activitySource = activitySource;
        _ollamaService = ollamaService;
    }
    
    [HttpPost("complete")]
    public async Task<IActionResult> Complete([FromBody] CompletionRequest request)
    {
        using var activity = _activitySource.StartActivity("llm.complete");
        
        try
        {
            var model = request.Model ?? "llama2";
            
            // Add span attributes
            activity?.SetTag("llm.model", model);
            activity?.SetTag("llm.prompt_length", request.Prompt.Length);
            
            var startTime = DateTime.UtcNow;
            
            // Call Ollama
            var completion = await _ollamaService.GenerateAsync(
                request.Prompt,
                model,
                request.MaxTokens
            );
            
            var latency = (DateTime.UtcNow - startTime).TotalMilliseconds;
            
            activity?.SetTag("llm.completion_length", completion.Length);
            activity?.SetTag("llm.latency_ms", latency);
            
            return Ok(new CompletionResponse
            {
                Completion = completion,
                Model = model,
                LatencyMs = (long)latency
            });
        }
        catch (Exception ex)
        {
            activity?.RecordException(ex);
            return StatusCode(500, new { error = ex.Message });
        }
    }
}
```

#### Key Differences from Python

- **ASP.NET Core**: Modern, cross-platform web framework
- **Async/Await**: Built-in async support similar to Python
- **Dependency Injection**: Built into the framework
- **Strong Typing**: Compile-time type safety

#### Challenges

- Different ecosystem and tooling
- Less AI/ML library support than Python
- More complex project structure

---

## Component Alternatives

### Vector Databases

If ChromaDB doesn't have good support in your language:

| Database | Languages | Notes |
|----------|-----------|-------|
| **Qdrant** | Python, Go, Rust, JS | Good multi-language support, gRPC API |
| **Weaviate** | Python, Go, Java, JS | GraphQL API, good documentation |
| **Pinecone** | Python, JS, Java | Managed service, easy to use |
| **Milvus** | Python, Go, Java, Node | Open source, scalable |
| **pgvector** | Any (PostgreSQL) | PostgreSQL extension, SQL interface |

### LLM Providers

Alternatives to Ollama:

| Provider | Notes |
|----------|-------|
| **OpenAI API** | Cloud-based, requires API key |
| **Anthropic Claude** | Cloud-based, requires API key |
| **Local LLMs** | llama.cpp, vLLM, text-generation-webui |
| **Hugging Face** | Transformers library, many models |

### Web Frameworks

| Language | Frameworks |
|----------|------------|
| **Node.js** | Express, Fastify, NestJS, Koa |
| **Go** | Gin, Echo, Fiber, Chi |
| **Java** | Spring Boot, Quarkus, Micronaut |
| **C#** | ASP.NET Core, Nancy |

## Common Challenges

### 1. OpenTelemetry SDK Differences

Each language's OpenTelemetry SDK has slightly different APIs:

**Python:**
```python
from opentelemetry import trace
span = trace.get_current_span()
span.set_attribute("key", "value")
```

**Node.js:**
```typescript
import { trace } from '@opentelemetry/api';
const span = trace.getActiveSpan();
span?.setAttribute("key", "value");
```

**Go:**
```go
import "go.opentelemetry.io/otel/trace"
span := trace.SpanFromContext(ctx)
span.SetAttributes(attribute.String("key", "value"))
```

### 2. Async/Sync Differences

- **Python**: Sync by default, async optional
- **Node.js**: Async by default
- **Go**: Goroutines for concurrency
- **Java/C#**: Thread-based with async/await

### 3. Error Handling

Different languages have different error handling patterns:

- **Python**: Exceptions
- **Go**: Error returns
- **Java/C#**: Exceptions with try-catch
- **Node.js**: Promises/async-await with try-catch

### 4. Type Systems

- **Python**: Dynamic typing (with optional type hints)
- **TypeScript**: Static typing with inference
- **Go/Java/C#**: Static typing

## Best Practices

Regardless of language:

1. **Initialize tracing early** in application startup
2. **Use context propagation** to maintain trace continuity
3. **Add meaningful attributes** to spans
4. **Handle errors gracefully** and record them in spans
5. **Test trace generation** in development
6. **Monitor trace export** to ensure data reaches OpenLLMetry
7. **Document your implementation** for future maintainers

## Resources

### OpenTelemetry Documentation

- [Python](https://opentelemetry.io/docs/instrumentation/python/)
- [JavaScript](https://opentelemetry.io/docs/instrumentation/js/)
- [Go](https://opentelemetry.io/docs/instrumentation/go/)
- [Java](https://opentelemetry.io/docs/instrumentation/java/)
- [.NET](https://opentelemetry.io/docs/instrumentation/net/)

### Example Repositories

Look for OpenTelemetry examples in your target language:
- [OpenTelemetry Demo](https://github.com/open-telemetry/opentelemetry-demo)
- Language-specific instrumentation examples

---

**Made with Bob**