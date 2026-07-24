# AgentTrace API

FastAPI service for ingesting and querying AI-agent trace data.

## Responsibilities

- Create agent runs
- Ingest trace events
- Store LLM calls, tool calls, guardrail checks, and errors
- Calculate run-level counters
- Expose metrics for the dashboard

## Run Locally

Start PostgreSQL from the repository root:

```bash
docker compose up -d
```

Then run the API:

```bash
cd agent-trace-api
cp .env.example .env
uv sync --dev
uv run uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Tests

```bash
uv run pytest
```
