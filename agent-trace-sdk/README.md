# AgentTrace SDK

Python SDK for instrumenting demo agents and emitting trace data to the AgentTrace API.

## Usage

```python
from agent_trace import AgentTraceClient

client = AgentTraceClient(base_url="http://127.0.0.1:8000")

with client.run(agent_name="demo-agent", user_input="Research AI observability") as run:
    run.llm_call_completed(
        step_name="planning",
        model="mock-llm",
        provider="mock",
        prompt_tokens=1000,
        completion_tokens=300,
        latency_ms=850,
    )
    run.tool_call_completed(
        step_name="web_search",
        tool_name="web_search",
        input={"query": "AI agent observability"},
        output_summary="Found 5 sources",
        latency_ms=320,
    )
```

## Run Demo Agent

Start the API first, then run:

```bash
uv sync --dev
uv run python examples/demo_agent.py
```
