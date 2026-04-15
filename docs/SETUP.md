# Setup Guide

This guide provides step-by-step instructions for setting up the OpenTelemetry AI Tracing prototype.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

1. **Python 3.12+**
   ```bash
   python --version
   # Should output: Python 3.12.x or higher
   ```

2. **uv** (Python package manager)
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Verify installation
   uv --version
   ```

3. **Ollama** (Local LLM runtime)
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Verify installation
   ollama --version
   ```

4. **Git** (for cloning the repository)
   ```bash
   git --version
   ```

### Optional Software

- **Podman** or **Docker** (if you want to containerize the application)
- **curl** or **Postman** (for testing API endpoints)

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd opentelemetry-testing
```

### Step 2: Install Python Dependencies

Using `uv` (recommended):

```bash
# Install all dependencies
uv sync

# This will create a virtual environment and install all packages
```

Alternatively, using pip:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Set Up Ollama

1. **Start Ollama service:**
   ```bash
   ollama serve
   ```
   
   Leave this running in a separate terminal window.

2. **Pull the required model:**
   ```bash
   # In a new terminal
   ollama pull llama2
   
   # Optional: Pull alternative models
   ollama pull mistral
   ```

3. **Verify Ollama is working:**
   ```bash
   ollama list
   # Should show llama2 in the list
   ```

### Step 4: Set Up OpenLLMetry Account

1. **Sign up for OpenLLMetry:**
   - Visit [https://www.traceloop.com/](https://www.traceloop.com/)
   - Create a free account
   - Navigate to your dashboard

2. **Get your API key:**
   - Go to Settings → API Keys
   - Create a new API key
   - Copy the key (you'll need it in the next step)

## Configuration

### Step 1: Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### Step 2: Configure Environment Variables

Edit the `.env` file with your settings:

```bash
# Application Settings
FLASK_ENV=development
FLASK_DEBUG=true
PORT=5000

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=30

# ChromaDB Configuration
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=documents

# OpenLLMetry Configuration (REQUIRED)
TRACELOOP_API_KEY=your_api_key_here  # Replace with your actual API key
TRACELOOP_DISABLE_BATCH=false

# OpenTelemetry Configuration
OTEL_SERVICE_NAME=ai-tracing-prototype
OTEL_LOG_LEVEL=info
```

**Important:** Replace `your_api_key_here` with your actual OpenLLMetry API key.

### Step 3: Prepare Sample Documents

The application comes with sample documents in `data/sample_docs.txt`. You can:

1. **Use the provided samples** (recommended for testing)
2. **Add your own documents:**
   ```bash
   # Edit or replace the file
   nano data/sample_docs.txt
   ```

## Running the Application

### Step 1: Start Ollama (if not already running)

```bash
# In a separate terminal
ollama serve
```

### Step 2: Start the Flask Application

Using `uv`:

```bash
uv run python run.py
```

Or with activated virtual environment:

```bash
python run.py
```

You should see output similar to:

```
INFO:app.telemetry:Initializing Traceloop SDK...
INFO:app.telemetry:Traceloop SDK initialized successfully
INFO:werkzeug: * Running on http://127.0.0.1:5000
```

### Step 3: Ingest Sample Documents (First Time Only)

In a new terminal, run the ingestion script:

```bash
# Using uv
uv run python -c "from app.rag_service import ingest_documents; ingest_documents('data/sample_docs.txt')"

# Or with activated venv
python -c "from app.rag_service import ingest_documents; ingest_documents('data/sample_docs.txt')"
```

Or use the Python REPL:

```python
from app.rag_service import ingest_documents
result = ingest_documents('data/sample_docs.txt')
print(result)
```

## Verification

### Test 1: Health Check

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ai-tracing-prototype",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Test 2: LLM Completion

```bash
curl -X POST http://localhost:5000/api/llm/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is OpenTelemetry?",
    "max_tokens": 50
  }'
```

Expected response:
```json
{
  "completion": "OpenTelemetry is an observability framework...",
  "model": "llama2",
  "tokens": 45,
  "prompt_tokens": 10,
  "completion_tokens": 35,
  "latency_ms": 1234
}
```

### Test 3: RAG Query

```bash
curl -X POST http://localhost:5000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does tracing work?",
    "top_k": 3
  }'
```

Expected response:
```json
{
  "query": "How does tracing work?",
  "retrieved_docs": [
    {
      "text": "Tracing allows you to track requests...",
      "score": 0.95,
      "metadata": {"source": "data/sample_docs.txt"}
    }
  ],
  "answer": "Based on the documentation, tracing works by...",
  "model": "llama2",
  "tokens": 120,
  "latency_ms": 2345
}
```

### Test 4: Verify Traces in OpenLLMetry

1. Open your OpenLLMetry dashboard: [https://app.traceloop.com/](https://app.traceloop.com/)
2. Navigate to the Traces section
3. You should see traces for your API calls
4. Click on a trace to see the span hierarchy and attributes

## Troubleshooting

### Issue: "Connection refused" when accessing the application

**Solution:**
- Ensure the Flask application is running: `python run.py`
- Check that the port 5000 is not in use by another application
- Try accessing `http://127.0.0.1:5000` instead of `localhost`

### Issue: "Ollama not available" error

**Solution:**
1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```
2. If not running, start it:
   ```bash
   ollama serve
   ```
3. Verify the model is pulled:
   ```bash
   ollama list
   ```
4. If model is missing, pull it:
   ```bash
   ollama pull llama2
   ```

### Issue: "Model not available" error

**Solution:**
- Pull the required model:
  ```bash
  ollama pull llama2
  ```
- Or specify a different model in your `.env` file:
  ```bash
  OLLAMA_MODEL=mistral
  ```
  Then pull that model:
  ```bash
  ollama pull mistral
  ```

### Issue: No traces appearing in OpenLLMetry

**Solution:**
1. Verify your API key is correct in `.env`
2. Check the application logs for trace export errors
3. Ensure you're making requests to the API endpoints (traces are only generated for requests)
4. Wait a few seconds - traces may take time to appear in the dashboard
5. Check your OpenLLMetry account quota/limits

### Issue: ChromaDB errors

**Solution:**
1. Delete the ChromaDB directory and reinitialize:
   ```bash
   rm -rf chroma_db
   ```
2. Restart the application
3. Re-ingest documents

### Issue: Import errors or missing dependencies

**Solution:**
1. Ensure you're using the correct Python version:
   ```bash
   python --version  # Should be 3.12+
   ```
2. Reinstall dependencies:
   ```bash
   uv sync --reinstall
   ```
3. If using pip, try:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

### Issue: Port 5000 already in use

**Solution:**
1. Change the port in `.env`:
   ```bash
   PORT=5001
   ```
2. Or kill the process using port 5000:
   ```bash
   # Find the process
   lsof -i :5000
   # Kill it
   kill -9 <PID>
   ```

## Running Tests

To verify everything is working correctly, run the test suite:

```bash
# Using uv
uv run pytest tests/ -v

# Or with activated venv
pytest tests/ -v
```

All tests should pass. If any tests fail, check the error messages and ensure:
- All dependencies are installed
- Configuration is correct
- No conflicting services are running

## Next Steps

Once setup is complete:

1. Review the [API Documentation](API.md) for detailed endpoint information
2. Check the [Language Implementation Guide](LANGUAGES.md) for adapting to other languages
3. Explore the OpenLLMetry dashboard to understand trace data
4. Experiment with different prompts and queries
5. Try different models (mistral, codellama, etc.)

## Additional Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenLLMetry Documentation](https://www.traceloop.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

## Getting Help

If you encounter issues not covered in this guide:

1. Check the application logs for detailed error messages
2. Review the GitHub issues for similar problems
3. Consult the official documentation for each component
4. Open a new issue with detailed information about your problem

---

**Made with Bob**