# Trace Model

AgentTrace models an AI-agent execution as a run composed of ordered trace events.

## Main Entities

### Agent Run

An `agent_run` represents one complete execution of an agent task.

Fields include:

- `id`
- `agent_name`
- `user_input`
- `status`
- `started_at`
- `ended_at`
- `duration_ms`
- aggregate counters
- estimated cost

### Trace Event

A `trace_event` represents one event in a run timeline.

Common event types:

```text
run_started
llm_call_started
llm_call_completed
tool_call_started
tool_call_completed
guardrail_check
run_completed
run_failed
```

### LLM Call

An `llm_call` stores metadata about one model request.

Fields include:

- model
- provider
- prompt tokens
- completion tokens
- total tokens
- estimated cost
- latency
- status
- error message

### Tool Call

A `tool_call` stores metadata about one tool execution.

Fields include:

- tool name
- input JSON
- output summary
- latency
- status
- error message

### Guardrail Check

A `guardrail_check` records a policy or safety decision.

Fields include:

- check name
- decision
- risk level
- reason

### Error

An `error` record allows fast filtering of failures across all runs.

Fields include:

- error type
- message
- component
- related run
- related event

## Timeline Principle

The timeline is ordered by `trace_events.timestamp`. Specialized tables such as `llm_calls`, `tool_calls`, and `guardrail_checks` attach additional structured metadata to timeline events.
