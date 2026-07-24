import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { AgentRun, ErrorRecord, MetricsSummary, TimelineResponse, api } from './api';

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function StatusBadge({ status }: { status: string }) {
  return <span className={`status status-${status}`}>{status}</span>;
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
    </div>
  );
}

function TimelineMetadata({ item }: { item: TimelineResponse['timeline'][number] }) {
  const detail = item.llm_call || item.tool_call || item.guardrail_check || item.error || item.event.metadata_json;
  if (!detail) return null;
  return <pre className="metadata">{JSON.stringify(detail, null, 2)}</pre>;
}

export default function App() {
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [errors, setErrors] = useState<ErrorRecord[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadDashboard() {
    try {
      setErrorMessage(null);
      const [summaryData, runData, errorData] = await Promise.all([
        api.getSummary(),
        api.getRuns(),
        api.getErrors(),
      ]);
      setSummary(summaryData);
      setRuns(runData);
      setErrors(errorData);
      if (!selectedRunId && runData.length > 0) {
        setSelectedRunId(runData[0].id);
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to load dashboard data');
    }
  }

  async function loadTimeline(runId: string) {
    try {
      const data = await api.getTimeline(runId);
      setTimeline(data);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to load timeline');
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      loadTimeline(selectedRunId);
    }
  }, [selectedRunId]);

  const chartData = summary
    ? [
        { name: 'LLM calls', value: summary.total_llm_calls },
        { name: 'Tool calls', value: summary.total_tool_calls },
        { name: 'Guardrails', value: summary.total_guardrail_checks },
        { name: 'Errors', value: summary.total_errors },
      ]
    : [];

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">AI Agent Observability</p>
          <h1>AgentTrace</h1>
          <p className="hero-text">
            Inspect agent runs, model calls, tool usage, guardrail decisions, errors, latency,
            and execution timelines from one local dashboard.
          </p>
        </div>
        <button className="refresh-button" onClick={loadDashboard}>Refresh</button>
      </header>

      {errorMessage && <div className="error-banner">{errorMessage}</div>}

      {summary && (
        <section className="metrics-grid">
          <MetricCard label="Total runs" value={summary.total_runs} />
          <MetricCard label="Successful" value={summary.successful_runs} />
          <MetricCard label="Failed" value={summary.failed_runs} />
          <MetricCard label="Avg latency" value={`${summary.average_duration_ms} ms`} />
          <MetricCard label="Estimated cost" value={`$${summary.estimated_cost_usd.toFixed(6)}`} />
        </section>
      )}

      <section className="panel chart-panel">
        <h2>Execution Activity</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="content-grid">
        <div className="panel">
          <h2>Runs</h2>
          <div className="run-list">
            {runs.map((run) => (
              <button
                key={run.id}
                className={`run-row ${run.id === selectedRunId ? 'selected' : ''}`}
                onClick={() => setSelectedRunId(run.id)}
              >
                <div className="run-row-top">
                  <strong>{run.agent_name}</strong>
                  <StatusBadge status={run.status} />
                </div>
                <p>{run.user_input}</p>
                <small>{formatDate(run.started_at)} · {run.total_steps} steps</small>
              </button>
            ))}
            {runs.length === 0 && <p className="empty">No runs yet. Run the demo agent first.</p>}
          </div>
        </div>

        <div className="panel timeline-panel">
          <h2>Run Timeline</h2>
          {timeline ? (
            <div className="timeline">
              <div className="selected-run-summary">
                <strong>{timeline.run.agent_name}</strong>
                <StatusBadge status={timeline.run.status} />
                <p>{timeline.run.user_input}</p>
              </div>
              {timeline.timeline.map((item) => (
                <article key={item.event.id} className="timeline-item">
                  <div className="timeline-dot" />
                  <div className="timeline-card">
                    <div className="timeline-card-header">
                      <strong>{item.event.event_type}</strong>
                      <StatusBadge status={item.event.status} />
                    </div>
                    <p>{item.event.step_name || 'unnamed step'}</p>
                    <small>
                      {formatDate(item.event.timestamp)}
                      {item.event.duration_ms !== null ? ` · ${item.event.duration_ms} ms` : ''}
                    </small>
                    <TimelineMetadata item={item} />
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty">Select a run to view its timeline.</p>
          )}
        </div>
      </section>

      <section className="panel">
        <h2>Errors</h2>
        {errors.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Component</th>
                <th>Message</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {errors.map((error) => (
                <tr key={error.id}>
                  <td>{error.error_type}</td>
                  <td>{error.component || '-'}</td>
                  <td>{error.message}</td>
                  <td>{formatDate(error.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty">No errors recorded.</p>
        )}
      </section>
    </main>
  );
}
