# Observability Integration Guide

This guide explains how to integrate the OpenTelemetry AI Tracing application with various observability platforms: Traceloop (OpenLLMetry), Langfuse, and Grafana.

> 💡 **Looking for deployment guidance?** Check out the [Deployment Scenarios Guide](DEPLOYMENT_SCENARIOS.md) for specific setup instructions for local, cloud, and hybrid deployments with cost analysis.

## Table of Contents

- [Overview](#overview)
- [Traceloop (OpenLLMetry)](#traceloop-openllmetry)
- [Langfuse Integration](#langfuse-integration)
- [Grafana Integration](#grafana-integration)
- [Multi-Platform Setup](#multi-platform-setup)
- [Cloud Deployments](#cloud-deployments)
- [Comparison Matrix](#comparison-matrix)

## Overview

This application supports multiple observability platforms for AI/LLM tracing and monitoring:

| Platform | Purpose | Best For | Deployment |
|----------|---------|----------|------------|
| **Traceloop** | AI-specific tracing | LLM observability, prompt tracking | Cloud (SaaS) |
| **Langfuse** | LLM analytics | Cost tracking, prompt management | Self-hosted or Cloud |
| **Grafana** | Metrics & visualization | System metrics, custom dashboards | Self-hosted or Cloud |

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Flask Application                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │         OpenTelemetry SDK                          │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │ │
│  │  │Traceloop │  │ Langfuse │  │   Grafana    │   │ │
│  │  │Exporter  │  │ Exporter │  │   Exporter   │   │ │
│  │  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │ │
│  └───────┼─────────────┼────────────────┼───────────┘ │
└──────────┼─────────────┼────────────────┼─────────────┘
           │             │                │
           ▼             ▼                ▼
    ┌──────────┐  ┌──────────┐    ┌──────────┐
    │Traceloop │  │ Langfuse │    │ Grafana  │
    │  Cloud   │  │  Server  │    │  Stack   │
    └──────────┘  └──────────┘    └──────────┘
```

---

## Traceloop (OpenLLMetry)

**Status:** ✅ Already Integrated (Cloud-Only Service)

Traceloop is a cloud-based SaaS platform that provides AI-specific observability. It cannot run locally and requires an API key from traceloop.com.

### Features

- ✅ Automatic LLM call tracing
- ✅ Prompt and completion tracking
- ✅ Token usage monitoring
- ✅ Latency analysis
- ✅ Error tracking
- ✅ Span hierarchy visualization

### Local Setup

1. **Sign up for Traceloop:**
   - Visit [https://www.traceloop.com/](https://www.traceloop.com/)
   - Create a free account
   - Get your API key from Settings → API Keys

2. **Configure environment:**
   ```bash
   # In .env file
   TRACELOOP_API_KEY=your_api_key_here
   TRACELOOP_DISABLE_BATCH=false
   OTEL_SERVICE_NAME=ai-tracing-prototype
   ```

3. **Verify integration:**
   ```bash
   # Start the application
   uv run python run.py
   
   # Make a test request
   curl -X POST http://localhost:5000/api/llm/complete \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, world!"}'
   
   # Check traces at https://app.traceloop.com/
   ```

### Cloud Deployment

Traceloop is a SaaS platform - no additional deployment needed. Simply configure your API key in production:

```bash
# Production environment variables
TRACELOOP_API_KEY=prod_api_key_here
OTEL_SERVICE_NAME=ai-tracing-prod
```

### Viewing Traces

1. Open [https://app.traceloop.com/](https://app.traceloop.com/)
2. Navigate to **Traces** section
3. Filter by service name or time range
4. Click on traces to see detailed span information

---

## Langfuse Integration

**Status:** 🔧 Configuration Required

Langfuse provides open-source LLM observability with advanced analytics and prompt management.

### Features

- 📊 Cost tracking and analytics
- 🎯 Prompt versioning and management
- 📈 User feedback collection
- 🔍 Advanced filtering and search
- 💰 Token usage and cost analysis
- 🏷️ Custom tagging and metadata

### Local Setup (Self-Hosted)

#### Option 1: Using Docker Compose

1. **Create Langfuse deployment:**
   ```bash
   # Create a docker-compose.yml for Langfuse
   mkdir langfuse-local
   cd langfuse-local
   ```

2. **Create `docker-compose.yml`:**
   ```yaml
   version: '3.8'
   
   services:
     langfuse-server:
       image: langfuse/langfuse:latest
       ports:
         - "3000:3000"
       environment:
         - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
         - NEXTAUTH_URL=http://localhost:3000
         - NEXTAUTH_SECRET=your-secret-key-change-this
         - SALT=your-salt-change-this
       depends_on:
         - db
   
     db:
       image: postgres:15
       environment:
         - POSTGRES_USER=postgres
         - POSTGRES_PASSWORD=postgres
         - POSTGRES_DB=langfuse
       volumes:
         - langfuse-db:/var/lib/postgresql/data
   
   volumes:
     langfuse-db:
   ```

3. **Start Langfuse:**
   ```bash
   podman-compose up -d
   # or
   docker-compose up -d
   ```

4. **Access Langfuse:**
   - Open http://localhost:3000
   - Create an account
   - Create a new project
   - Get API keys from Settings

#### Option 2: Using Langfuse Cloud

1. Sign up at [https://cloud.langfuse.com/](https://cloud.langfuse.com/)
2. Create a project
3. Get your API keys

### Application Integration

1. **Install Langfuse SDK:**
   ```bash
   uv add langfuse
   ```

2. **Update `pyproject.toml`:**
   ```toml
   dependencies = [
       # ... existing dependencies ...
       "langfuse>=2.0.0",
   ]
   ```

3. **Create `app/langfuse_integration.py`:**
   ```python
   """Langfuse integration for LLM observability using HTTP API."""
   
   import logging
   import requests
   import uuid
   from datetime import datetime
   from app.config import Config
   
   logger = logging.getLogger(__name__)
   
   def configure_langfuse_otlp():
       """Log that Langfuse is configured via HTTP API."""
       if Config.LANGFUSE_PUBLIC_KEY and Config.LANGFUSE_SECRET_KEY:
           logger.info(f"Langfuse HTTP API configured for {Config.LANGFUSE_HOST}")
       else:
           logger.warning("Langfuse keys not configured")
   
   def trace_llm_call(prompt: str, completion: str, model: str,
                      tokens: int, latency_ms: int):
       """
       Trace an LLM call to Langfuse using the HTTP API.
       Creates a generation observation that will appear in Langfuse UI.
       
       Important: Uses 'prompt' and 'completion' fields (not 'input'/'output')
       to ensure data is properly stored in the database.
       """
       public_key = Config.LANGFUSE_PUBLIC_KEY
       secret_key = Config.LANGFUSE_SECRET_KEY
       host = Config.LANGFUSE_HOST
       
       if not public_key or not secret_key:
           return
       
       try:
           # Generate IDs
           trace_id = str(uuid.uuid4())
           generation_id = str(uuid.uuid4())
           timestamp = datetime.utcnow().isoformat() + "Z"
           
           # Create trace via HTTP API
           trace_data = {
               "id": trace_id,
               "name": "llm_completion",
               "timestamp": timestamp,
               "metadata": {"source": "ollama"}
           }
           
           # Create generation via HTTP API
           # Note: Use 'prompt' and 'completion' fields for text to be stored
           generation_data = {
               "id": generation_id,
               "traceId": trace_id,
               "type": "GENERATION",
               "name": "ollama_generation",
               "startTime": timestamp,
               "endTime": timestamp,
               "model": model,
               "prompt": prompt,
               "completion": completion,
               "usage": {
                   "total": tokens
               },
               "metadata": {
                   "latency_ms": latency_ms
               }
           }
           
           # Send to Langfuse
           auth = (public_key, secret_key)
           
           # Create trace
           response = requests.post(
               f"{host}/api/public/traces",
               json=trace_data,
               auth=auth,
               timeout=5
           )
           response.raise_for_status()
           
           # Create generation
           response = requests.post(
               f"{host}/api/public/generations",
               json=generation_data,
               auth=auth,
               timeout=5
           )
           response.raise_for_status()
           
           logger.info(f"Traced LLM call to Langfuse: {model}, {tokens} tokens")
       except Exception as exc:
           logger.error(f"Failed to trace to Langfuse: {exc}")
   ```
   
   **Important Note**: The Langfuse API requires using `prompt` and `completion` field names (not `input` and `output`) for the data to be properly stored in the database. In the Langfuse UI, you must click on the generation observation (not the trace level) to see the full prompt and response.

4. **Update `app/config.py`:**
   ```python
   # Add to Config class
   LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
   LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
   LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
   ```

5. **Update `.env.example`:**
   ```bash
   # Langfuse Configuration (Optional)
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=http://localhost:3000
   ```

6. **Integrate in `app/llm_service.py`:**
   ```python
   from app.langfuse_integration import trace_llm_call
   
   # In generate_completion function, after successful completion:
   trace_llm_call(
       prompt=prompt,
       completion=completion,
       model=selected_model,
       tokens=total_tokens,
       latency_ms=latency_ms
   )
   ```

### Cloud Deployment

**Langfuse Cloud:**
```bash
# Production environment
LANGFUSE_PUBLIC_KEY=pk-lf-prod-...
LANGFUSE_SECRET_KEY=sk-lf-prod-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Self-Hosted on Cloud:**
- Deploy using Docker on AWS ECS, Google Cloud Run, or Azure Container Instances
- Use managed PostgreSQL (RDS, Cloud SQL, Azure Database)
- Configure SSL/TLS certificates
- Set up proper authentication

---

## Grafana Integration

**Status:** 🔧 Configuration Required

Grafana provides powerful visualization and alerting for metrics and traces.

### Features

- 📊 Custom dashboards
- 🔔 Alerting and notifications
- 📈 Metrics visualization
- 🔍 Trace exploration
- 📉 Performance monitoring
- 🎯 SLO tracking

### Local Setup (Grafana Stack)

#### Option 1: Using Docker Compose (Recommended)

1. **Create Grafana stack deployment:**
   ```bash
   mkdir grafana-stack
   cd grafana-stack
   ```

2. **Create `docker-compose.yml`:**
   ```yaml
   version: '3.8'
   
   services:
     # Grafana for visualization
     grafana:
       image: grafana/grafana:latest
       ports:
         - "3003:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=admin
         - GF_USERS_ALLOW_SIGN_UP=false
       volumes:
         - grafana-data:/var/lib/grafana
         - ./grafana/provisioning:/etc/grafana/provisioning
   
     # Prometheus for metrics
     prometheus:
       image: prom/prometheus:latest
       ports:
         - "9090:9090"
       volumes:
         - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
         - prometheus-data:/prometheus
       command:
         - '--config.file=/etc/prometheus/prometheus.yml'
         - '--storage.tsdb.path=/prometheus'
   
     # Tempo for traces
     tempo:
       image: grafana/tempo:latest
       ports:
         - "3200:3200"   # Tempo
         - "4317:4317"   # OTLP gRPC
         - "4318:4318"   # OTLP HTTP
       volumes:
         - ./tempo/tempo.yaml:/etc/tempo.yaml
         - tempo-data:/var/tempo
       command: ["-config.file=/etc/tempo.yaml"]
   
     # Loki for logs (optional)
     loki:
       image: grafana/loki:latest
       ports:
         - "3100:3100"
       volumes:
         - ./loki/loki.yaml:/etc/loki/local-config.yaml
         - loki-data:/loki
       command: -config.file=/etc/loki/local-config.yaml
   
   volumes:
     grafana-data:
     prometheus-data:
     tempo-data:
     loki-data:
   ```

3. **Create Prometheus config (`prometheus/prometheus.yml`):**
   ```yaml
   global:
     scrape_interval: 15s
     evaluation_interval: 15s
   
   scrape_configs:
     - job_name: 'ai-tracing-app'
       static_configs:
         - targets: ['host.docker.internal:5000']
       metrics_path: '/metrics'
   ```

4. **Create Tempo config (`tempo/tempo.yaml`):**
   ```yaml
   server:
     http_listen_port: 3200
   
   distributor:
     receivers:
       otlp:
         protocols:
           grpc:
             endpoint: 0.0.0.0:4317
           http:
             endpoint: 0.0.0.0:4318
   
   storage:
     trace:
       backend: local
       local:
         path: /var/tempo/traces
   ```

5. **Create Loki config (`loki/loki.yaml`):**
   ```yaml
   auth_enabled: false
   
   server:
     http_listen_port: 3100
   
   ingester:
     lifecycler:
       ring:
         kvstore:
           store: inmemory
         replication_factor: 1
   
   schema_config:
     configs:
       - from: 2020-10-24
         store: boltdb-shipper
         object_store: filesystem
         schema: v11
         index:
           prefix: index_
           period: 24h
   
   storage_config:
     boltdb_shipper:
       active_index_directory: /loki/boltdb-shipper-active
       cache_location: /loki/boltdb-shipper-cache
       shared_store: filesystem
     filesystem:
       directory: /loki/chunks
   ```

6. **Start the stack:**
   ```bash
   podman-compose up -d
   # or
   docker-compose up -d
   ```

7. **Access services:**
   - Grafana: http://localhost:3003 (admin/admin)
   - Prometheus: http://localhost:9090
   - Tempo: http://localhost:3200

### Application Integration

1. **Install OpenTelemetry exporters:**
   ```bash
   uv add opentelemetry-exporter-otlp \
          opentelemetry-exporter-prometheus \
          prometheus-client
   ```

2. **Update `pyproject.toml`:**
   ```toml
   dependencies = [
       # ... existing dependencies ...
       "opentelemetry-exporter-otlp>=1.22.0",
       "opentelemetry-exporter-prometheus>=0.43b0",
       "prometheus-client>=0.19.0",
   ]
   ```

3. **Create `app/grafana_integration.py`:**
   ```python
   """Grafana/Prometheus/Tempo integration."""
   
   import logging
   from opentelemetry import metrics, trace
   from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
   from opentelemetry.exporter.prometheus import PrometheusMetricReader
   from opentelemetry.sdk.metrics import MeterProvider
   from opentelemetry.sdk.trace import TracerProvider
   from opentelemetry.sdk.trace.export import BatchSpanProcessor
   from prometheus_client import make_wsgi_app
   from werkzeug.middleware.dispatcher import DispatcherMiddleware
   
   from app.config import Config
   
   logger = logging.getLogger(__name__)
   
   def initialize_grafana_telemetry(app):
       """Initialize Grafana/Tempo/Prometheus integration."""
       
       # Configure Tempo (traces)
       if Config.TEMPO_ENDPOINT:
           try:
               trace_provider = TracerProvider()
               otlp_exporter = OTLPSpanExporter(
                   endpoint=Config.TEMPO_ENDPOINT,
                   insecure=True
               )
               trace_provider.add_span_processor(
                   BatchSpanProcessor(otlp_exporter)
               )
               trace.set_tracer_provider(trace_provider)
               logger.info(f"Tempo exporter configured: {Config.TEMPO_ENDPOINT}")
           except Exception as exc:
               logger.error(f"Failed to configure Tempo: {exc}")
       
       # Configure Prometheus (metrics)
       try:
           metric_reader = PrometheusMetricReader()
           meter_provider = MeterProvider(metric_readers=[metric_reader])
           metrics.set_meter_provider(meter_provider)
           
           # Add Prometheus metrics endpoint
           app.wsgi_app = DispatcherMiddleware(
               app.wsgi_app,
               {'/metrics': make_wsgi_app()}
           )
           logger.info("Prometheus metrics endpoint configured at /metrics")
       except Exception as exc:
           logger.error(f"Failed to configure Prometheus: {exc}")
   ```

4. **Update `app/config.py`:**
   ```python
   # Add to Config class
   TEMPO_ENDPOINT = os.getenv("TEMPO_ENDPOINT", "http://localhost:4317")
   ENABLE_GRAFANA = os.getenv("ENABLE_GRAFANA", "false").lower() == "true"
   ```

5. **Update `.env.example`:**
   ```bash
   # Grafana/Tempo Configuration (Optional)
   ENABLE_GRAFANA=true
   TEMPO_ENDPOINT=http://localhost:4317
   ```

6. **Update `app/__init__.py`:**
   ```python
   from app.grafana_integration import initialize_grafana_telemetry
   
   # After telemetry initialization
   if Config.ENABLE_GRAFANA:
       initialize_grafana_telemetry(app)
   ```

### Grafana Dashboard Setup

1. **Access Grafana:** http://localhost:3003
2. **Add data sources:**
   - Prometheus: http://prometheus:9090
   - Tempo: http://tempo:3200
   - Loki: http://loki:3100

3. **Import dashboard:**
   - Go to Dashboards → Import
   - Use dashboard ID or upload JSON
   - Configure data sources

4. **Create custom dashboard:**
   ```json
   {
     "dashboard": {
       "title": "AI Tracing Metrics",
       "panels": [
         {
           "title": "LLM Request Rate",
           "targets": [
             {
               "expr": "rate(llm_requests_total[5m])"
             }
           ]
         },
         {
           "title": "Average Latency",
           "targets": [
             {
               "expr": "avg(llm_latency_ms)"
             }
           ]
         },
         {
           "title": "Token Usage",
           "targets": [
             {
               "expr": "sum(llm_tokens_total)"
             }
           ]
         }
       ]
     }
   }
   ```

### Cloud Deployment

**Grafana Cloud:**
```bash
# Sign up at https://grafana.com/
# Get your credentials
GRAFANA_CLOUD_INSTANCE_ID=your-instance
GRAFANA_CLOUD_API_KEY=your-api-key
TEMPO_ENDPOINT=https://tempo-prod-us-central-0.grafana.net:443
```

**Self-Hosted on Cloud:**
- Deploy on Kubernetes using Helm charts
- Use managed services (AWS Managed Grafana, Azure Managed Grafana)
- Configure persistent storage
- Set up load balancing and SSL

---

## Multi-Platform Setup

You can use multiple observability platforms simultaneously for comprehensive monitoring.

### Configuration Example

```bash
# .env file with all platforms enabled

# Traceloop (AI-specific)
TRACELOOP_API_KEY=your_traceloop_key
TRACELOOP_DISABLE_BATCH=false

# Langfuse (LLM analytics)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# Grafana Stack (metrics & visualization)
ENABLE_GRAFANA=true
TEMPO_ENDPOINT=http://localhost:4317

# OpenTelemetry
OTEL_SERVICE_NAME=ai-tracing-prototype
```

### Benefits of Multi-Platform Approach

| Platform | Primary Use Case | Complementary Platforms |
|----------|------------------|------------------------|
| **Traceloop** | Quick AI insights, production monitoring | Langfuse (cost), Grafana (infra) |
| **Langfuse** | Cost analysis, prompt management | Traceloop (traces), Grafana (metrics) |
| **Grafana** | Infrastructure metrics, custom dashboards | Traceloop (AI), Langfuse (LLM) |

---

## Cloud Deployments

### AWS Deployment

#### Using AWS ECS + Managed Services

```yaml
# docker-compose-aws.yml
version: '3.8'

services:
  app:
    image: your-registry/ai-tracing-app:latest
    environment:
      # Traceloop (SaaS)
      - TRACELOOP_API_KEY=${TRACELOOP_API_KEY}
      
      # Langfuse on ECS
      - LANGFUSE_HOST=https://langfuse.your-domain.com
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      
      # AWS Managed Grafana
      - TEMPO_ENDPOINT=https://tempo.your-region.amazonaws.com:4317
      - ENABLE_GRAFANA=true
```

**Services to use:**
- ECS/Fargate for application
- RDS PostgreSQL for Langfuse
- AWS Managed Grafana
- CloudWatch for logs

### Google Cloud Deployment

#### Using Cloud Run + GCP Services

```yaml
# cloud-run-config.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ai-tracing-app
spec:
  template:
    spec:
      containers:
      - image: gcr.io/your-project/ai-tracing-app
        env:
        - name: TRACELOOP_API_KEY
          valueFrom:
            secretKeyRef:
              name: traceloop-secret
              key: api-key
        - name: LANGFUSE_HOST
          value: "https://langfuse.your-domain.com"
        - name: TEMPO_ENDPOINT
          value: "https://tempo.your-region.gcp.com:4317"
```

**Services to use:**
- Cloud Run for application
- Cloud SQL for Langfuse
- GKE for Grafana stack
- Cloud Logging

### Azure Deployment

#### Using Container Instances + Azure Services

```yaml
# azure-container-instance.yaml
apiVersion: 2021-09-01
location: eastus
name: ai-tracing-app
properties:
  containers:
  - name: app
    properties:
      image: your-registry.azurecr.io/ai-tracing-app:latest
      environmentVariables:
      - name: TRACELOOP_API_KEY
        secureValue: ${TRACELOOP_API_KEY}
      - name: LANGFUSE_HOST
        value: https://langfuse.your-domain.com
      - name: TEMPO_ENDPOINT
        value: https://tempo.your-region.azure.com:4317
```

**Services to use:**
- Container Instances or AKS
- Azure Database for PostgreSQL
- Azure Managed Grafana
- Application Insights

---

## Comparison Matrix

### Feature Comparison

| Feature | Traceloop | Langfuse | Grafana |
|---------|-----------|----------|---------|
| **AI/LLM Tracing** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Cost Tracking** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Prompt Management** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| **Custom Dashboards** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Alerting** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Self-Hosted Option** | ❌ | ✅ | ✅ |
| **Free Tier** | ✅ | ✅ | ✅ |
| **Setup Complexity** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

### Cost Comparison

| Platform | Free Tier | Paid Plans | Self-Hosted Cost |
|----------|-----------|------------|------------------|
| **Traceloop** | 100K spans/month | From $49/month | N/A |
| **Langfuse** | Unlimited (self-hosted) | From $49/month | Infrastructure only |
| **Grafana** | 10K series (cloud) | From $49/month | Infrastructure only |

### Recommendation by Use Case

| Use Case | Recommended Platform(s) |
|----------|------------------------|
| **Quick Start** | Traceloop only |
| **Cost Optimization** | Langfuse + Grafana |
| **Enterprise** | All three platforms |
| **Self-Hosted** | Langfuse + Grafana |
| **AI-First** | Traceloop + Langfuse |

---

## Troubleshooting

### Traceloop Issues

**No traces appearing:**
- Verify API key is correct
- Check network connectivity
- Review application logs for export errors
- Ensure requests are being made to the API

### Langfuse Issues

**Connection errors:**
```bash
# Check Langfuse is running
curl http://localhost:3000/api/public/health

# Check database connection
podman logs langfuse-server
```

**Authentication failures:**
- Verify API keys are correct
- Check project ID matches
- Ensure keys have proper permissions

### Grafana Issues

**No metrics appearing:**
```bash
# Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Verify metrics endpoint
curl http://localhost:5000/metrics
```

**Tempo not receiving traces:**
```bash
# Check Tempo is running
curl http://localhost:3200/ready

# Verify OTLP endpoint
curl http://localhost:4318/v1/traces
```

---

## Next Steps

1. **Start with Traceloop** - Already integrated, easiest to use
2. **Add Langfuse** - For cost tracking and prompt management
3. **Integrate Grafana** - For comprehensive metrics and custom dashboards
4. **Explore dashboards** - Create custom visualizations
5. **Set up alerts** - Configure notifications for issues
6. **Optimize costs** - Use insights to reduce token usage

## Additional Resources

- [Traceloop Documentation](https://www.traceloop.com/docs)
- [Langfuse Documentation](https://langfuse.com/docs)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Tempo Documentation](https://grafana.com/docs/tempo/)

---

**Made with Bob** 🤖