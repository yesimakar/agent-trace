from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class AgentTraceError(RuntimeError):
    pass


@dataclass
class AgentTraceClient:
    base_url: str = os.getenv("AGENT_TRACE_API_URL", "http://127.0.0.1:8000")
    timeout: float = 10.0

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def create_run(
        self,
        agent_name: str,
        user_input: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = httpx.post(
            self._url("/api/runs"),
            json={"agent_name": agent_name, "user_input": user_input, "metadata": metadata},
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise AgentTraceError(f"Failed to create run: {response.status_code} {response.text}")
        return response.json()

    def emit_event(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            self._url(f"/api/runs/{run_id}/events"),
            json=payload,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise AgentTraceError(f"Failed to emit event: {response.status_code} {response.text}")
        return response.json()

    def run(
        self,
        agent_name: str,
        user_input: str,
        metadata: dict[str, Any] | None = None,
    ) -> "TraceRunContext":
        return TraceRunContext(self, agent_name, user_input, metadata)


class TraceRunContext:
    def __init__(
        self,
        client: AgentTraceClient,
        agent_name: str,
        user_input: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.client = client
        self.agent_name = agent_name
        self.user_input = user_input
        self.metadata = metadata
        self.run_id: str | None = None

    def __enter__(self) -> "TraceRunContext":
        run = self.client.create_run(self.agent_name, self.user_input, self.metadata)
        self.run_id = run["id"]
        self.event("run_started", step_name="start", status="started")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc:
            self.error(
                error_type=exc_type.__name__ if exc_type else "UnknownError",
                message=str(exc),
                component="agent",
                step_name="run_failed",
            )
            return False
        self.event("run_completed", step_name="complete", status="success")
        return False

    def _require_run_id(self) -> str:
        if not self.run_id:
            raise AgentTraceError("Run has not been started")
        return self.run_id

    def event(
        self,
        event_type: str,
        step_name: str | None = None,
        status: str = "success",
        duration_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.client.emit_event(
            self._require_run_id(),
            {
                "event_type": event_type,
                "step_name": step_name,
                "status": status,
                "duration_ms": duration_ms,
                "metadata": metadata,
            },
        )

    def llm_call_completed(
        self,
        step_name: str,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        status: str = "success",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.client.emit_event(
            self._require_run_id(),
            {
                "event_type": "llm_call_completed",
                "step_name": step_name,
                "status": status,
                "duration_ms": latency_ms,
                "metadata": metadata,
                "llm_call": {
                    "model": model,
                    "provider": provider,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "latency_ms": latency_ms,
                    "status": status,
                },
            },
        )

    def tool_call_completed(
        self,
        step_name: str,
        tool_name: str,
        input: dict[str, Any] | None,
        output_summary: str,
        latency_ms: int,
        status: str = "success",
    ) -> dict[str, Any]:
        return self.client.emit_event(
            self._require_run_id(),
            {
                "event_type": "tool_call_completed",
                "step_name": step_name,
                "status": status,
                "duration_ms": latency_ms,
                "tool_call": {
                    "tool_name": tool_name,
                    "input": input,
                    "output_summary": output_summary,
                    "latency_ms": latency_ms,
                    "status": status,
                },
            },
        )

    def guardrail_check(
        self,
        check_name: str,
        decision: str,
        risk_level: str,
        reason: str,
    ) -> dict[str, Any]:
        return self.client.emit_event(
            self._require_run_id(),
            {
                "event_type": "guardrail_check",
                "step_name": check_name,
                "status": "success",
                "guardrail_check": {
                    "check_name": check_name,
                    "decision": decision,
                    "risk_level": risk_level,
                    "reason": reason,
                },
            },
        )

    def error(
        self,
        error_type: str,
        message: str,
        component: str,
        step_name: str | None = None,
    ) -> dict[str, Any]:
        return self.client.emit_event(
            self._require_run_id(),
            {
                "event_type": "run_failed",
                "step_name": step_name,
                "status": "failed",
                "error": {
                    "error_type": error_type,
                    "message": message,
                    "component": component,
                },
            },
        )
