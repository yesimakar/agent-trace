def create_run(client):
    response = client.post(
        "/api/runs",
        json={"agent_name": "demo-agent", "user_input": "Research AI observability"},
    )
    assert response.status_code == 201
    return response.json()


def test_create_run(client):
    run = create_run(client)
    assert run["agent_name"] == "demo-agent"
    assert run["status"] == "running"


def test_ingest_llm_tool_guardrail_events_and_timeline(client):
    run = create_run(client)
    run_id = run["id"]

    llm_response = client.post(
        f"/api/runs/{run_id}/events",
        json={
            "event_type": "llm_call_completed",
            "step_name": "planning",
            "status": "success",
            "duration_ms": 850,
            "llm_call": {
                "model": "mock-llm",
                "provider": "mock",
                "prompt_tokens": 1000,
                "completion_tokens": 300,
                "latency_ms": 850,
            },
        },
    )
    assert llm_response.status_code == 201

    tool_response = client.post(
        f"/api/runs/{run_id}/events",
        json={
            "event_type": "tool_call_completed",
            "step_name": "web_search",
            "status": "success",
            "duration_ms": 300,
            "tool_call": {
                "tool_name": "web_search",
                "input": {"query": "agent observability"},
                "output_summary": "Found 5 sources",
                "latency_ms": 300,
            },
        },
    )
    assert tool_response.status_code == 201

    guardrail_response = client.post(
        f"/api/runs/{run_id}/events",
        json={
            "event_type": "guardrail_check",
            "step_name": "prompt_injection_check",
            "status": "success",
            "guardrail_check": {
                "check_name": "prompt_injection_check",
                "decision": "passed",
                "risk_level": "low",
                "reason": "No injection indicators detected",
            },
        },
    )
    assert guardrail_response.status_code == 201

    complete = client.post(
        f"/api/runs/{run_id}/events",
        json={"event_type": "run_completed", "step_name": "final", "status": "success"},
    )
    assert complete.status_code == 201

    timeline = client.get(f"/api/runs/{run_id}/timeline")
    assert timeline.status_code == 200
    body = timeline.json()
    assert body["run"]["status"] == "completed"
    assert len(body["timeline"]) == 4


def test_error_event_marks_run_failed(client):
    run = create_run(client)
    run_id = run["id"]

    response = client.post(
        f"/api/runs/{run_id}/events",
        json={
            "event_type": "run_failed",
            "step_name": "web_search",
            "status": "failed",
            "error": {
                "error_type": "ToolExecutionError",
                "message": "Search provider unavailable",
                "component": "web_search",
            },
        },
    )
    assert response.status_code == 201

    errors = client.get("/api/errors")
    assert errors.status_code == 200
    assert len(errors.json()) == 1

    run_response = client.get(f"/api/runs/{run_id}")
    assert run_response.json()["status"] == "failed"
