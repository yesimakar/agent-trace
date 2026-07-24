from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RunStatus = Literal["running", "completed", "failed"]
EventStatus = Literal["started", "success", "failed", "blocked", "warning"]


class RunCreate(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=200)
    user_input: str = Field(..., min_length=1)
    metadata: dict[str, Any] | None = None


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_name: str
    user_input: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_ms: int | None
    total_steps: int
    total_llm_calls: int
    total_tool_calls: int
    total_guardrail_checks: int
    total_errors: int
    estimated_cost_usd: float
    metadata_json: dict[str, Any] | None
    created_at: datetime


class LLMCallCreate(BaseModel):
    model: str = Field(..., min_length=1)
    provider: str = "mock"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int | None = None
    status: str = "success"
    error_message: str | None = None
    estimated_cost_usd: float | None = None


class ToolCallCreate(BaseModel):
    tool_name: str = Field(..., min_length=1)
    input: dict[str, Any] | None = None
    output_summary: str | None = None
    latency_ms: int | None = None
    status: str = "success"
    error_message: str | None = None


class GuardrailCheckCreate(BaseModel):
    check_name: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    risk_level: str = Field(..., min_length=1)
    reason: str | None = None


class ErrorCreate(BaseModel):
    error_type: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    component: str | None = None


class TraceEventCreate(BaseModel):
    event_type: str = Field(..., min_length=1)
    step_name: str | None = None
    status: EventStatus = "success"
    duration_ms: int | None = None
    metadata: dict[str, Any] | None = None
    llm_call: LLMCallCreate | None = None
    tool_call: ToolCallCreate | None = None
    guardrail_check: GuardrailCheckCreate | None = None
    error: ErrorCreate | None = None


class TraceEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    event_type: str
    step_name: str | None
    status: str
    timestamp: datetime
    duration_ms: int | None
    metadata_json: dict[str, Any] | None
    created_at: datetime


class TimelineItem(BaseModel):
    event: TraceEventRead
    llm_call: dict[str, Any] | None = None
    tool_call: dict[str, Any] | None = None
    guardrail_check: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class TimelineResponse(BaseModel):
    run: RunRead
    timeline: list[TimelineItem]


class MetricsSummary(BaseModel):
    total_runs: int
    successful_runs: int
    failed_runs: int
    running_runs: int
    average_duration_ms: float
    total_llm_calls: int
    total_tool_calls: int
    total_guardrail_checks: int
    total_errors: int
    estimated_cost_usd: float


class ToolUsageMetric(BaseModel):
    tool_name: str
    calls: int
    average_latency_ms: float
    failures: int


class ModelUsageMetric(BaseModel):
    model: str
    provider: str
    calls: int
    total_tokens: int
    estimated_cost_usd: float
    average_latency_ms: float


class ErrorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    event_id: str
    error_type: str
    message: str
    component: str | None
    created_at: datetime
