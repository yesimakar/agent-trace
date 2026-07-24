const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export type AgentRun = {
  id: string;
  agent_name: string;
  user_input: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  total_steps: number;
  total_llm_calls: number;
  total_tool_calls: number;
  total_guardrail_checks: number;
  total_errors: number;
  estimated_cost_usd: number;
};

export type MetricsSummary = {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  running_runs: number;
  average_duration_ms: number;
  total_llm_calls: number;
  total_tool_calls: number;
  total_guardrail_checks: number;
  total_errors: number;
  estimated_cost_usd: number;
};

export type TimelineItem = {
  event: {
    id: string;
    event_type: string;
    step_name: string | null;
    status: string;
    timestamp: string;
    duration_ms: number | null;
    metadata_json: Record<string, unknown> | null;
  };
  llm_call?: Record<string, unknown> | null;
  tool_call?: Record<string, unknown> | null;
  guardrail_check?: Record<string, unknown> | null;
  error?: Record<string, unknown> | null;
};

export type TimelineResponse = {
  run: AgentRun;
  timeline: TimelineItem[];
};

export type ErrorRecord = {
  id: string;
  run_id: string;
  event_id: string;
  error_type: string;
  message: string;
  component: string | null;
  created_at: string;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  getSummary: () => getJson<MetricsSummary>('/api/metrics/summary'),
  getRuns: () => getJson<AgentRun[]>('/api/runs'),
  getTimeline: (runId: string) => getJson<TimelineResponse>(`/api/runs/${runId}/timeline`),
  getErrors: () => getJson<ErrorRecord[]>('/api/errors'),
};
