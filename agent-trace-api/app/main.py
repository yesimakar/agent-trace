from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db
from app.models import AgentRun, ErrorRecord, GuardrailCheck, LLMCall, ToolCall, TraceEvent
from app.schemas import (
    ErrorRead,
    MetricsSummary,
    ModelUsageMetric,
    RunCreate,
    RunRead,
    TimelineItem,
    TimelineResponse,
    ToolUsageMetric,
    TraceEventCreate,
    TraceEventRead,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AgentTrace API",
    version="0.1.0",
    description="Trace ingestion, persistence, and metrics API for AI-agent observability.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent-trace-api"}


def _get_run_or_404(db: Session, run_id: str) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


def _estimate_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    # Simple MVP estimate. Production systems should use provider/model-specific pricing.
    total_tokens = prompt_tokens + completion_tokens
    return round((total_tokens / 1_000_000) * 2.50, 6)


def _recalculate_run(db: Session, run: AgentRun) -> None:
    events = db.query(TraceEvent).filter(TraceEvent.run_id == run.id).all()
    llm_calls = db.query(LLMCall).filter(LLMCall.run_id == run.id).all()
    tool_calls = db.query(ToolCall).filter(ToolCall.run_id == run.id).all()
    guardrails = db.query(GuardrailCheck).filter(GuardrailCheck.run_id == run.id).all()
    errors = db.query(ErrorRecord).filter(ErrorRecord.run_id == run.id).all()

    run.total_steps = len(events)
    run.total_llm_calls = len(llm_calls)
    run.total_tool_calls = len(tool_calls)
    run.total_guardrail_checks = len(guardrails)
    run.total_errors = len(errors)
    run.estimated_cost_usd = round(sum(call.estimated_cost_usd for call in llm_calls), 6)

    if run.ended_at:
        run.duration_ms = int((run.ended_at - run.started_at).total_seconds() * 1000)


@app.post("/api/runs", response_model=RunRead, status_code=201)
def create_run(payload: RunCreate, db: Session = Depends(get_db)) -> AgentRun:
    run = AgentRun(
        agent_name=payload.agent_name,
        user_input=payload.user_input,
        status="running",
        metadata_json=payload.metadata,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@app.get("/api/runs", response_model=list[RunRead])
def list_runs(limit: int = 50, db: Session = Depends(get_db)) -> list[AgentRun]:
    return (
        db.query(AgentRun)
        .order_by(AgentRun.started_at.desc())
        .limit(min(limit, 200))
        .all()
    )


@app.get("/api/runs/{run_id}", response_model=RunRead)
def get_run(run_id: str, db: Session = Depends(get_db)) -> AgentRun:
    return _get_run_or_404(db, run_id)


@app.post("/api/runs/{run_id}/events", response_model=TraceEventRead, status_code=201)
def create_event(run_id: str, payload: TraceEventCreate, db: Session = Depends(get_db)) -> TraceEvent:
    run = _get_run_or_404(db, run_id)

    event = TraceEvent(
        run_id=run.id,
        event_type=payload.event_type,
        step_name=payload.step_name,
        status=payload.status,
        duration_ms=payload.duration_ms,
        metadata_json=payload.metadata,
    )
    db.add(event)
    db.flush()

    if payload.llm_call:
        total_tokens = payload.llm_call.prompt_tokens + payload.llm_call.completion_tokens
        estimated_cost = payload.llm_call.estimated_cost_usd
        if estimated_cost is None:
            estimated_cost = _estimate_cost_usd(
                payload.llm_call.prompt_tokens,
                payload.llm_call.completion_tokens,
            )
        db.add(
            LLMCall(
                run_id=run.id,
                event_id=event.id,
                model=payload.llm_call.model,
                provider=payload.llm_call.provider,
                prompt_tokens=payload.llm_call.prompt_tokens,
                completion_tokens=payload.llm_call.completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=estimated_cost,
                latency_ms=payload.llm_call.latency_ms,
                status=payload.llm_call.status,
                error_message=payload.llm_call.error_message,
            )
        )

    if payload.tool_call:
        db.add(
            ToolCall(
                run_id=run.id,
                event_id=event.id,
                tool_name=payload.tool_call.tool_name,
                input_json=payload.tool_call.input,
                output_summary=payload.tool_call.output_summary,
                latency_ms=payload.tool_call.latency_ms,
                status=payload.tool_call.status,
                error_message=payload.tool_call.error_message,
            )
        )

    if payload.guardrail_check:
        db.add(
            GuardrailCheck(
                run_id=run.id,
                event_id=event.id,
                check_name=payload.guardrail_check.check_name,
                decision=payload.guardrail_check.decision,
                risk_level=payload.guardrail_check.risk_level,
                reason=payload.guardrail_check.reason,
            )
        )

    if payload.error:
        db.add(
            ErrorRecord(
                run_id=run.id,
                event_id=event.id,
                error_type=payload.error.error_type,
                message=payload.error.message,
                component=payload.error.component,
            )
        )
        run.status = "failed"
        run.ended_at = datetime.now(UTC).replace(tzinfo=None)

    if payload.event_type == "run_completed":
        run.status = "completed"
        run.ended_at = datetime.now(UTC).replace(tzinfo=None)
    elif payload.event_type == "run_failed":
        run.status = "failed"
        run.ended_at = datetime.now(UTC).replace(tzinfo=None)

    _recalculate_run(db, run)
    db.commit()
    db.refresh(event)
    return event


def _model_to_dict(obj: Any, exclude: set[str] | None = None) -> dict[str, Any]:
    exclude = exclude or set()
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns if column.name not in exclude}


@app.get("/api/runs/{run_id}/timeline", response_model=TimelineResponse)
def get_timeline(run_id: str, db: Session = Depends(get_db)) -> TimelineResponse:
    run = _get_run_or_404(db, run_id)
    events = (
        db.query(TraceEvent)
        .filter(TraceEvent.run_id == run.id)
        .order_by(TraceEvent.timestamp.asc())
        .all()
    )

    items: list[TimelineItem] = []
    for event in events:
        llm = db.query(LLMCall).filter(LLMCall.event_id == event.id).first()
        tool = db.query(ToolCall).filter(ToolCall.event_id == event.id).first()
        guardrail = db.query(GuardrailCheck).filter(GuardrailCheck.event_id == event.id).first()
        error = db.query(ErrorRecord).filter(ErrorRecord.event_id == event.id).first()
        items.append(
            TimelineItem(
                event=TraceEventRead.model_validate(event),
                llm_call=_model_to_dict(llm) if llm else None,
                tool_call=_model_to_dict(tool) if tool else None,
                guardrail_check=_model_to_dict(guardrail) if guardrail else None,
                error=_model_to_dict(error) if error else None,
            )
        )

    return TimelineResponse(run=RunRead.model_validate(run), timeline=items)


@app.get("/api/metrics/summary", response_model=MetricsSummary)
def metrics_summary(db: Session = Depends(get_db)) -> MetricsSummary:
    runs = db.query(AgentRun).all()
    completed_durations = [run.duration_ms for run in runs if run.duration_ms is not None]
    average_duration = sum(completed_durations) / len(completed_durations) if completed_durations else 0.0

    return MetricsSummary(
        total_runs=len(runs),
        successful_runs=sum(1 for run in runs if run.status == "completed"),
        failed_runs=sum(1 for run in runs if run.status == "failed"),
        running_runs=sum(1 for run in runs if run.status == "running"),
        average_duration_ms=round(average_duration, 2),
        total_llm_calls=sum(run.total_llm_calls for run in runs),
        total_tool_calls=sum(run.total_tool_calls for run in runs),
        total_guardrail_checks=sum(run.total_guardrail_checks for run in runs),
        total_errors=sum(run.total_errors for run in runs),
        estimated_cost_usd=round(sum(run.estimated_cost_usd for run in runs), 6),
    )


@app.get("/api/metrics/tools", response_model=list[ToolUsageMetric])
def tool_metrics(db: Session = Depends(get_db)) -> list[ToolUsageMetric]:
    rows = (
        db.query(
            ToolCall.tool_name,
            func.count(ToolCall.id),
            func.avg(ToolCall.latency_ms),
            func.sum(case((ToolCall.status == "failed", 1), else_=0)),
        )
        .group_by(ToolCall.tool_name)
        .all()
    )
    return [
        ToolUsageMetric(
            tool_name=row[0],
            calls=row[1],
            average_latency_ms=round(float(row[2] or 0), 2),
            failures=int(row[3] or 0),
        )
        for row in rows
    ]


@app.get("/api/metrics/models", response_model=list[ModelUsageMetric])
def model_metrics(db: Session = Depends(get_db)) -> list[ModelUsageMetric]:
    rows = (
        db.query(
            LLMCall.model,
            LLMCall.provider,
            func.count(LLMCall.id),
            func.sum(LLMCall.total_tokens),
            func.sum(LLMCall.estimated_cost_usd),
            func.avg(LLMCall.latency_ms),
        )
        .group_by(LLMCall.model, LLMCall.provider)
        .all()
    )
    return [
        ModelUsageMetric(
            model=row[0],
            provider=row[1],
            calls=row[2],
            total_tokens=int(row[3] or 0),
            estimated_cost_usd=round(float(row[4] or 0), 6),
            average_latency_ms=round(float(row[5] or 0), 2),
        )
        for row in rows
    ]


@app.get("/api/errors", response_model=list[ErrorRead])
def list_errors(limit: int = 100, db: Session = Depends(get_db)) -> list[ErrorRecord]:
    return (
        db.query(ErrorRecord)
        .order_by(ErrorRecord.created_at.desc())
        .limit(min(limit, 500))
        .all()
    )
