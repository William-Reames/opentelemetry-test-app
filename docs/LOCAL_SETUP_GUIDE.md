# Local Setup Guide for Observability Integration

This guide will help you set up Traceloop, Langfuse, and Grafana for local development and testing.

## Prerequisites

- Docker installed and running
- Python 3.12+ with uv package manager
- Ollama running locally (for LLM functionality)

## Quick Start

### 1. Install Python Dependencies

The required dependencies have been added to `pyproject.toml`. Install them using:

```bash
# If uv is available in your PATH
uv sync

# If uv is not in PATH, you may need to install it first or use pip in a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Start Langfuse (Port 3002)

Langfuse provides LLM analytics and cost tracking:

```bash
cd langfuse-local
docker compose up -d
```

Wait for Langfuse to start (about 30 seconds), then:
- Open http://localhost:3002
- Create an account
- Create a new project
- Go to Settings → API Keys
- Copy your Public Key and Secret Key

### 3. Start Grafana Stack

The Grafana stack includes Grafana, Prometheus, Tempo, and Loki:

```bash
cd ../grafana-stack
docker compose up -d
```

Services will be available at:
- **Grafana**: http://localhost:3003 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Tempo**: http://localhost:3200
- **Loki**: http://localhost:3100

### 4. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and configure:

```bash
# Traceloop Configuration
TRACELOOP_API_KEY=your_traceloop_api_key_here

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...  # From Langfuse UI
LANGFUSE_SECRET_KEY=sk-lf-...  # From Langfuse UI
LANGFUSE_HOST=http://localhost:3002

# Grafana/Tempo Configuration
ENABLE_GRAFANA=true
TEMPO_ENDPOINT=http://localhost:4317

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
```

### 5. Start the Application

```bash
python run.py
```

The application will start on http://localhost:5000

## Verifying the Setup

### Test Traceloop

1. Sign up at https://www.traceloop.com/ and get your API key
2. Add it to your `.env` file
3. Make a test request:

```bash
curl -X POST http://localhost:5000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'
```

4. Check traces at https://app.traceloop.com/

### Test Langfuse

1. Make a test request (same as above)
2. Open http://localhost:3002
3. Login with `test@localhost.local` / `password123`
4. Navigate to "Tracing" → "Traces"
5. Click on any "llm_completion" trace
6. **Important**: Click on the "ollama_generation" item (marked as GENERATION) to see the full prompt and response
   - The trace-level view shows "null" for input/output (this is normal)
   - The actual prompt and completion are in the generation observation

**Note**: The Langfuse API keys are pre-configured in the setup:
- Public Key: `pk-lf-1a758d87-062d-4774-ae86-c92a56eff716`
- Secret Key: `sk-lf-021b11a2-1819-4a21-a7d2-cb8638fd3113`

### Test Grafana/Prometheus

1. Open http://localhost:3003 (login: admin/admin)
2. Go to Configuration → Data Sources
3. Add Prometheus:
   - URL: http://prometheus:9090
   - Click "Save & Test"
4. Add Tempo:
   - URL: http://tempo:3200
   - Click "Save & Test"
5. Check metrics endpoint:

```bash
curl http://localhost:5000/metrics
```

## Troubleshooting

### Langfuse Not Starting

If you see "port already allocated" error:
- Check what's using port 3002: `lsof -i :3002`
- Stop the conflicting service or change the port in `langfuse-local/docker-compose.yml`

### Grafana Stack Network Issues

If Docker has network timeout issues:
- Check your internet connection
- Try again: `docker compose up -d`
- Or pull images manually: `docker compose pull`

### Python Dependencies Not Installing

If `uv` is not available:
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Or use pip in a virtual environment (see step 1 above)

### No Traces Appearing

1. **Traceloop**: Verify API key is correct in `.env`
2. **Langfuse**: Check that services are running: `docker ps | grep langfuse`
3. **Grafana**: Verify Tempo is receiving traces: `curl http://localhost:3200/ready`

## Service Management

### Stop All Services

```bash
# Stop Langfuse
cd langfuse-local && docker compose down

# Stop Grafana Stack
cd ../grafana-stack && docker compose down
```

### View Logs

```bash
# Langfuse logs
docker logs langfuse-local-langfuse-server-1

# Grafana logs
docker logs grafana-stack-grafana-1

# Tempo logs
docker logs grafana-stack-tempo-1
```

### Restart Services

```bash
# Restart Langfuse
cd langfuse-local && docker compose restart

# Restart Grafana Stack
cd ../grafana-stack && docker compose restart
```

## Next Steps

1. **Configure Grafana Dashboards**: Create custom dashboards for your metrics
2. **Set Up Alerts**: Configure alerting in Grafana for important metrics
3. **Explore Langfuse**: Use prompt management and cost tracking features
4. **Review Traces**: Analyze LLM performance in Traceloop

## Additional Resources

- [Traceloop Documentation](https://www.traceloop.com/docs)
- [Langfuse Documentation](https://langfuse.com/docs)
- [Grafana Documentation](https://grafana.com/docs/)
- [Full Integration Guide](./OBSERVABILITY_INTEGRATION.md)

---

**Made with Bob** 🤖