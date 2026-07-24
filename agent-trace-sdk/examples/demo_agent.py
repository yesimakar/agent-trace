import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_trace import AgentTraceClient  # noqa: E402


def pause(min_ms: int = 100, max_ms: int = 300) -> int:
    latency = random.randint(min_ms, max_ms)
    time.sleep(latency / 1000)
    return latency


def main() -> None:
    client = AgentTraceClient()
    user_input = "Research emerging practices in AI agent observability"

    with client.run(
        agent_name="demo-research-agent",
        user_input=user_input,
        metadata={"environment": "local-demo", "version": "0.1.0"},
    ) as run:
        latency = pause(500, 900)
        run.llm_call_completed(
            step_name="planning",
            model="mock-planner-llm",
            provider="mock",
            prompt_tokens=950,
            completion_tokens=220,
            latency_ms=latency,
            metadata={"purpose": "plan research steps"},
        )

        latency = pause(250, 500)
        run.tool_call_completed(
            step_name="web_search",
            tool_name="web_search",
            input={"query": "AI agent observability tracing tools"},
            output_summary="Found 5 relevant sources about agent traces, tool calls, and metrics.",
            latency_ms=latency,
        )

        latency = pause(150, 350)
        run.tool_call_completed(
            step_name="summarizer",
            tool_name="summarizer",
            input={"documents": 5},
            output_summary="Summarized sources into 6 key findings.",
            latency_ms=latency,
        )

        run.guardrail_check(
            check_name="prompt_injection_check",
            decision="passed",
            risk_level="low",
            reason="No suspicious instruction override patterns were detected in retrieved text.",
        )

        latency = pause(600, 1000)
        run.llm_call_completed(
            step_name="final_response",
            model="mock-writer-llm",
            provider="mock",
            prompt_tokens=1800,
            completion_tokens=650,
            latency_ms=latency,
            metadata={"purpose": "write final research summary"},
        )

    print("Demo trace generated successfully. Open the dashboard or API timeline to inspect it.")


if __name__ == "__main__":
    main()
