# Grafana Quick Start Guide

This guide will walk you through setting up Grafana to visualize your application metrics and traces.

## Step 1: Access Grafana

1. Open your browser and go to: **http://localhost:3003**
2. Login with:
   - **Username:** `admin`
   - **Password:** `admin`
3. You'll be prompted to change the password - you can skip this for local development

## Step 2: Add Prometheus Data Source

Prometheus collects metrics from your Flask application.

1. Click the **☰ menu** (hamburger icon) in the top left
2. Go to **Connections** → **Data sources**
3. Click **Add data source**
4. Select **Prometheus**
5. Configure:
   - **Name:** `Prometheus`
   - **URL:** `http://prometheus:9090`
   - Leave other settings as default
6. Click **Save & test** at the bottom
7. You should see: ✅ "Successfully queried the Prometheus API"

## Step 3: Add Tempo Data Source (Optional - for Traces)

Tempo stores distributed traces from your application.

1. Go back to **Connections** → **Data sources**
2. Click **Add data source**
3. Select **Tempo**
4. Configure:
   - **Name:** `Tempo`
   - **URL:** `http://tempo:3200`
   - Leave other settings as default
5. Click **Save & test**
6. You should see: ✅ "Data source successfully connected"

## Step 4: Explore Your Metrics

### Option A: Use Explore (Quick View)

1. Click **Explore** (compass icon) in the left sidebar
2. Select **Prometheus** from the dropdown at the top
3. Try these queries:

**View Python Version:**
```promql
python_info
```

**View Target Health:**
```promql
up{job="ai-tracing-app"}
```

**View Garbage Collection:**
```promql
rate(python_gc_collections_total[5m])
```

**View OpenTelemetry Metrics:**
```promql
otel_sdk_processor_span_queue_size
```

4. Click **Run query** to see the results

### Option B: Create a Dashboard

1. Click **Dashboards** (four squares icon) in the left sidebar
2. Click **New** → **New Dashboard**
3. Click **Add visualization**
4. Select **Prometheus** as the data source
5. Add a panel with this query:
   ```promql
   up{job="ai-tracing-app"}
   ```
6. Set the panel title to "Application Health"
7. Click **Apply**
8. Click **Save dashboard** (disk icon) at the top right
9. Name it "AI Tracing App Metrics"

## Step 5: View Application Metrics

Here are some useful metrics you can visualize:

### System Metrics

**Python Runtime Info:**
```promql
python_info
```

**Garbage Collection Rate:**
```promql
rate(python_gc_collections_total[5m])
```

**Process CPU Usage:**
```promql
rate(process_cpu_seconds_total[5m])
```

### OpenTelemetry Metrics

**Span Queue Size:**
```promql
otel_sdk_processor_span_queue_size
```

**Metric Collection Duration:**
```promql
otel_sdk_metric_reader_collection_duration_seconds
```

## Step 6: Create a Complete Dashboard

Here's a sample dashboard configuration you can import:

1. Click **Dashboards** → **New** → **Import**
2. Paste this JSON:

```json
{
  "dashboard": {
    "title": "AI Tracing Application",
    "panels": [
      {
        "id": 1,
        "title": "Application Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"ai-tracing-app\"}",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Python Version",
        "type": "stat",
        "targets": [
          {
            "expr": "python_info",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "GC Collections Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(python_gc_collections_total[5m])",
            "refId": "A",
            "legendFormat": "Generation {{generation}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
      },
      {
        "id": 4,
        "title": "Span Queue Size",
        "type": "graph",
        "targets": [
          {
            "expr": "otel_sdk_processor_span_queue_size",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4}
      }
    ]
  }
}
```

3. Click **Load**
4. Select **Prometheus** as the data source
5. Click **Import**

## Step 7: View Traces (When Available)

Once you start making LLM requests, traces will be sent to Tempo:

1. Click **Explore** in the left sidebar
2. Select **Tempo** from the dropdown
3. Click **Search** to see recent traces
4. Click on a trace to see the detailed span hierarchy

## Troubleshooting

### "Data source not found"
- Make sure Prometheus and Tempo containers are running:
  ```bash
  docker ps | grep -E "prometheus|tempo"
  ```

### "No data" in queries
- Verify metrics are being exposed:
  ```bash
  curl http://localhost:5000/metrics
  ```
- Check Prometheus is scraping:
  ```bash
  curl http://localhost:9090/api/v1/targets
  ```

### Can't connect to data sources
- Use `http://prometheus:9090` not `http://localhost:9090` (Docker network)
- Use `http://tempo:3200` not `http://localhost:3200` (Docker network)

## Next Steps

1. **Make some LLM requests** to generate more metrics:
   ```bash
   curl -X POST http://localhost:5000/api/llm/complete \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello", "model": "deepseek-r1", "max_tokens": 10}'
   ```

2. **Refresh your Grafana dashboard** to see updated metrics

3. **Create custom panels** for metrics that matter to you:
   - Request rates
   - Error rates
   - Latency percentiles
   - Token usage (when you add custom metrics)

4. **Set up alerts** for important thresholds:
   - Application down (up == 0)
   - High error rates
   - Performance degradation

## Useful Resources

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)

---

**Made with Bob** 🤖