# OpenTelemetry AI Tracing Prototype

A minimal working prototype demonstrating OpenTelemetry tracing integration with AI components, including LLM calls and RAG (Retrieval-Augmented Generation) queries.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

This project showcases how to implement comprehensive observability for AI applications using OpenTelemetry. It provides:

- **LLM Integration**: Direct integration with Ollama for local LLM inference
- **RAG Pipeline**: Complete retrieval-augmented generation with vector search
- **OpenTelemetry Tracing**: Full distributed tracing with span hierarchy
- **Multi-Platform Observability**: Support for Traceloop, Langfuse, and Grafana

### Observability Platforms

This application integrates with multiple observability platforms:

| Platform | Purpose | Status |
|----------|---------|--------|
| **[Traceloop](https://www.traceloop.com/)** | AI-specific tracing and monitoring | ✅ Integrated |
| **[Langfuse](https://langfuse.com/)** | LLM analytics and cost tracking | 🔧 Configuration available |
| **[Grafana](https://grafana.com/)** | Metrics visualization and dashboards | 🔧 Configuration available |

See the **[Observability Integration Guide](docs/OBSERVABILITY_INTEGRATION.md)** for detailed setup instructions for each platform.

### Key Features

✅ **Local & Free**: Runs entirely on your machine, no API keys required (except OpenLLMetry)  
✅ **Production-Ready Patterns**: Demonstrates best practices for AI observability  
✅ **Comprehensive Tracing**: Captures prompts, completions, tokens, latency, and more  
✅ **Easy to Adapt**: Clear code structure for porting to other languages  
✅ **Well Documented**: Extensive documentation and examples

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Ollama](https://ollama.com/) (Local LLM runtime)
- [OpenLLMetry](https://www.traceloop.com/) account (free tier available)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd opentelemetry-testing

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenLLMetry API key

# Start Ollama
ollama serve

# Pull the LLM model (in a new terminal)
ollama pull llama2

# Start the application
uv run python run.py
```

### First Request

```bash
# Test the health endpoint
curl http://localhost:5000/health

# Try an LLM completion
curl -X POST http://localhost:5000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is OpenTelemetry?"}'

# Ingest sample documents (first time only)
curl -X POST http://localhost:5000/api/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/sample_docs.txt"}'

# Try a RAG query
curl -X POST http://localhost:5000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does tracing work?"}'
```

### View Traces

1. Open your [OpenLLMetry dashboard](https://app.traceloop.com/)
2. Navigate to the Traces section
3. See your API calls with full span hierarchy and metadata

## 📚 Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration instructions
- **[API Documentation](docs/API.md)** - Complete API reference with examples
- **[Observability Integration](docs/OBSERVABILITY_INTEGRATION.md)** - Traceloop, Langfuse, and Grafana integration guide
- **[Deployment Scenarios](docs/DEPLOYMENT_SCENARIOS.md)** - Local and cloud deployment options with cost analysis
- **[Language Guide](docs/LANGUAGES.md)** - Notes for implementing in other languages

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────────┐
│         Flask Application           │
│  ┌──────────────────────────────┐  │
│  │   OpenTelemetry SDK          │  │
│  │   + Traceloop Integration    │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────┐      ┌────────────┐ │
│  │   LLM    │      │    RAG     │ │
│  │ Service  │      │  Service   │ │
│  └────┬─────┘      └─────┬──────┘ │
└───────┼──────────────────┼─────────┘
        │                  │
        ▼                  ▼
   ┌─────────┐      ┌──────────────┐
   │ Ollama  │      │  ChromaDB    │
   │  (LLM)  │      │  (Vectors)   │
   └─────────┘      └──────────────┘
        │                  │
        └──────────┬───────┘
                   │ Traces
                   ▼
          ┌─────────────────┐
          │  OpenLLMetry    │
          │   Dashboard     │
          └─────────────────┘
```

## 🔍 What Gets Traced?

### LLM Calls
- Model name and version
- Prompt and completion text
- Token counts (prompt, completion, total)
- Temperature and other parameters
- Latency and timing information
- Error details if failures occur

### RAG Queries
- Search query text
- Number of documents retrieved
- Similarity scores
- Context assembly
- Final LLM generation
- End-to-end latency

### HTTP Requests
- Request method and path
- Status codes
- Request/response timing
- Error information

## 📁 Project Structure

```
opentelemetry-testing/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── config.py            # Configuration management
│   ├── telemetry.py         # OpenTelemetry setup
│   ├── routes.py            # API endpoints
│   ├── llm_service.py       # Ollama integration
│   └── rag_service.py       # ChromaDB + RAG logic
├── data/
│   └── sample_docs.txt      # Sample documents for RAG
├── docs/
│   ├── SETUP.md             # Setup instructions
│   ├── API.md               # API documentation
│   └── LANGUAGES.md         # Alternative language notes
├── tests/
│   ├── test_llm.py          # LLM service tests
│   ├── test_rag.py          # RAG service tests
│   └── test_telemetry.py    # Telemetry tests
├── planning/
│   └── plan.md              # Project plan and tasks
├── .env.example             # Environment variables template
├── pyproject.toml           # Python project configuration
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── README.md                # This file
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_llm.py -v
```

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | Flask | HTTP API server |
| **LLM Provider** | Ollama | Local LLM inference |
| **Vector Database** | ChromaDB | Document embeddings and search |
| **Tracing** | OpenTelemetry | Distributed tracing |
| **Observability** | OpenLLMetry | AI-specific trace analysis |
| **Package Manager** | uv | Fast Python package management |

## 🎓 Learning Resources

### OpenTelemetry
- [Official Documentation](https://opentelemetry.io/docs/)
- [Python Instrumentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Tracing Concepts](https://opentelemetry.io/docs/concepts/signals/traces/)

### AI Observability
- [OpenLLMetry Documentation](https://www.traceloop.com/docs)
- [LLM Observability Best Practices](https://www.traceloop.com/blog)

### Components
- [Ollama Documentation](https://github.com/ollama/ollama)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone and install
git clone <repository-url>
cd opentelemetry-testing
uv sync

# Install development dependencies
uv add --dev pytest pytest-cov pytest-mock pylint black

# Run linting
uv run pylint app/

# Format code
uv run black app/ tests/
```

## 📝 Use Cases

This prototype demonstrates patterns useful for:

- **AI Application Monitoring**: Track LLM performance and costs
- **RAG Pipeline Debugging**: Understand retrieval quality and context assembly
- **Performance Optimization**: Identify bottlenecks in AI workflows
- **Error Tracking**: Capture and analyze AI-related failures
- **Cost Management**: Monitor token usage and API calls

## 🔒 Security Notes

This is a **prototype for local development**. Before deploying to production:

- [ ] Add authentication and authorization
- [ ] Implement rate limiting
- [ ] Secure API endpoints
- [ ] Validate and sanitize inputs
- [ ] Use environment-specific configurations
- [ ] Enable HTTPS/TLS
- [ ] Review and update dependencies
- [ ] Implement proper logging and monitoring

## 🐛 Troubleshooting

### Common Issues

**"Ollama not available"**
```bash
# Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

**"Model not available"**
```bash
# Pull the model
ollama pull llama2

# List available models
ollama list
```

**"No traces in OpenLLMetry"**
- Verify your API key in `.env`
- Check application logs for export errors
- Ensure you're making requests to the API
- Wait a few seconds for traces to appear

See [SETUP.md](docs/SETUP.md) for more troubleshooting tips.

## 📊 Performance

Expected latencies on a modern laptop:

- **Health Check**: < 10ms
- **LLM Completion**: 1-5 seconds (model dependent)
- **RAG Query**: 2-8 seconds (includes search + generation)
- **Trace Export**: < 100ms overhead

## 🗺️ Roadmap

Future enhancements:

- [ ] Add streaming support for LLM responses
- [ ] Implement caching for frequent queries
- [ ] Add more vector database options
- [ ] Support for multiple LLM providers
- [ ] Enhanced error recovery
- [ ] Performance benchmarking tools
- [ ] Docker/Podman containerization
- [ ] Kubernetes deployment examples

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [OpenTelemetry](https://opentelemetry.io/) for the observability framework
- [Traceloop](https://www.traceloop.com/) for OpenLLMetry
- [Ollama](https://ollama.com/) for local LLM inference
- [ChromaDB](https://www.trychroma.com/) for vector storage

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Made with Bob** 🤖
