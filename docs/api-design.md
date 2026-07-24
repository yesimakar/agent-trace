# API Design

The API is designed around trace ingestion and dashboard read operations.

## Health

```http
GET /health
```

Returns service status.

## Runs

```http
POST /api/runs
GET /api/runs
GET /api/runs/{run_id}
```

A run is created when an agent starts a task. The run is updated as events are ingested.

## Events

```http
POST /api/runs/{run_id}/events
GET /api/runs/{run_id}/timeline
```

Events represent the ordered execution timeline of an agent run.

## Metrics

```http
GET /api/metrics/summary
GET /api/metrics/tools
GET /api/metrics/models
```

Metrics are computed from persisted run, LLM, and tool records.

## Errors

```http
GET /api/errors
```

Returns captured failures across runs.

## Event Ingestion Payload

```json
{
  "event_type": "llm_call_completed",
  "step_name": "planning",
  "status": "success",
  "duration_ms": 850,
  "metadata": {
    "temperature": 0.2
  },
  "llm_call": {
    "model": "gpt-4.1",
    "provider": "openai",
    "prompt_tokens": 1200,
    "completion_tokens": 500,
    "latency_ms": 850,
    "status": "success"
  }
}
```

## API Design Principles

- Keep ingestion simple and explicit.
- Store raw metadata when useful.
- Normalize important records for metrics.
- Keep dashboard endpoints read-optimized.
- Avoid real authentication in the MVP to keep local setup simple.
