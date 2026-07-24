def test_metrics_summary(client):
    run_response = client.post(
        "/api/runs",
        json={"agent_name": "demo-agent", "user_input": "Research AI tracing"},
    )
    run_id = run_response.json()["id"]

    client.post(
        f"/api/runs/{run_id}/events",
        json={
            "event_type": "llm_call_completed",
            "step_name": "planning",
            "status": "success",
            "duration_ms": 500,
            "llm_call": {
                "model": "mock-llm",
                "provider": "mock",
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "latency_ms": 500,
            },
        },
    )
    client.post(
        f"/api/runs/{run_id}/events",
        json={
            "event_type": "tool_call_completed",
            "step_name": "summarizer",
            "status": "success",
            "tool_call": {
                "tool_name": "summarizer",
                "input": {"text": "sample"},
                "output_summary": "Summary generated",
                "latency_ms": 200,
            },
        },
    )
    client.post(
        f"/api/runs/{run_id}/events",
        json={"event_type": "run_completed", "status": "success"},
    )

    summary = client.get("/api/metrics/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["total_runs"] == 1
    assert body["successful_runs"] == 1
    assert body["total_llm_calls"] == 1
    assert body["total_tool_calls"] == 1

    tools = client.get("/api/metrics/tools")
    assert tools.status_code == 200
    assert tools.json()[0]["tool_name"] == "summarizer"

    models = client.get("/api/metrics/models")
    assert models.status_code == 200
    assert models.json()[0]["model"] == "mock-llm"
