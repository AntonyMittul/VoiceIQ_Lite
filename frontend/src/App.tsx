import { useEffect, useMemo, useState } from "react";
import { fetchMetrics, fetchTasks } from "./api";
import type { DashboardMetrics, Task } from "./types";

const emptyMetrics: DashboardMetrics = {
  total_tasks: 0,
  overdue_tasks: 0,
  completed_tasks: 0,
  completion_rate: 0,
  high_priority_open_tasks: 0,
  blocked_tasks: 0,
};

const formatDate = (value: string) => new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short" }).format(new Date(value));

function App() {
  const [metrics, setMetrics] = useState(emptyMetrics);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [status, setStatus] = useState("");
  const [region, setRegion] = useState("");
  const [priority, setPriority] = useState("");
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setError("");
      const filters = { status, region, priority };
      const [nextMetrics, nextTasks] = await Promise.all([fetchMetrics(), fetchTasks(filters)]);
      setMetrics(nextMetrics);
      setTasks(nextTasks);
      setSelectedTask((current) => current && nextTasks.some((task) => task.task_id === current.task_id) ? current : null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load dashboard data");
    }
  };

  useEffect(() => { void load(); }, [status, region, priority]);

  const riskQueue = useMemo(() => [...tasks].sort((a, b) => b.risk_score - a.risk_score).slice(0, 5), [tasks]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">V</span><div><strong>VoiceIQ</strong><small>LITE / OPS COPILOT</small></div></div>
        <nav><a className="active" href="#overview">Overview</a><a href="#risk-queue">Risk queue</a><a href="#tasks">All tasks</a><a className="muted" href="#assistant">Assistant <span>SOON</span></a></nav>
        <div className="sidebar-footer"><span className="status-dot" /> Synthetic demo data<br /><small>Governance mode enabled</small></div>
      </aside>
      <main className="content">
        <header className="topbar"><div><p className="eyebrow">THURSDAY, 24 SEPTEMBER 2026</p><h1>Operations cockpit</h1><p className="subtitle">A clear view of what needs attention today.</p></div><button className="refresh" onClick={() => void load()}>↻ Refresh data</button></header>
        {error && <div className="error-banner">{error}. Start the API and load demo data to populate the cockpit.</div>}
        <section className="metrics-grid" id="overview">
          <Metric label="Total tasks" value={metrics.total_tasks} note="Across all teams" />
          <Metric label="Overdue" value={metrics.overdue_tasks} note="Need immediate review" tone="danger" />
          <Metric label="Completion rate" value={`${metrics.completion_rate}%`} note={`${metrics.completed_tasks} completed`} tone="success" />
          <Metric label="High priority open" value={metrics.high_priority_open_tasks} note={`${metrics.blocked_tasks} currently blocked`} tone="warning" />
        </section>
        <section className="workspace-grid">
          <div className="panel queue-panel" id="risk-queue"><div className="panel-heading"><div><p className="eyebrow">PRIORITIZED WORK</p><h2>Risk queue</h2></div><span className="count-pill">{riskQueue.length} shown</span></div><p className="panel-description">Tasks ranked by transparent baseline risk factors.</p><div className="risk-list">{riskQueue.length ? riskQueue.map((task) => <button className={`risk-item ${selectedTask?.task_id === task.task_id ? "selected" : ""}`} key={task.task_id} onClick={() => setSelectedTask(task)}><span className={`risk-score ${task.risk_score >= 70 ? "high" : task.risk_score >= 40 ? "medium" : "low"}`}>{Math.round(task.risk_score)}</span><span className="risk-copy"><strong>{task.title}</strong><small>{task.task_id} · {task.region} · due {formatDate(task.due_date)}</small></span><span className="arrow">→</span></button>) : <EmptyState />}</div></div>
          <div className="panel detail-panel"><div className="panel-heading"><div><p className="eyebrow">TASK DETAIL</p><h2>{selectedTask ? selectedTask.task_id : "Select a task"}</h2></div>{selectedTask && <span className={`badge ${selectedTask.status}`}>{selectedTask.status.replace("_", " ")}</span>}</div>{selectedTask ? <div className="detail-content"><h3>{selectedTask.title}</h3><p className="detail-meta">{selectedTask.team} · {selectedTask.assignee} · {selectedTask.region}</p><div className="detail-risk"><span>Baseline risk score</span><strong>{Math.round(selectedTask.risk_score)}<small>/100</small></strong></div><div className="progress-label"><span>Progress</span><span>{selectedTask.progress_pct}%</span></div><div className="progress"><span style={{ width: `${selectedTask.progress_pct}%` }} /></div><div className="evidence"><p className="eyebrow">WHY IT IS RISKY</p><p>{selectedTask.is_overdue ? "Past due date" : "Due date approaching"}; {selectedTask.previous_delay_count} previous delay{selectedTask.previous_delay_count === 1 ? "" : "s"}; {selectedTask.blocker ? `blocker: ${selectedTask.blocker}` : "no blocker recorded"}.</p></div></div> : <EmptyState message="Choose an item from the risk queue to review its evidence." />}</div>
        </section>
        <section className="panel tasks-panel" id="tasks"><div className="panel-heading"><div><p className="eyebrow">WORK INVENTORY</p><h2>All tasks</h2></div><div className="filters"><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All statuses</option><option value="open">Open</option><option value="in_progress">In progress</option><option value="blocked">Blocked</option><option value="completed">Completed</option></select><select value={priority} onChange={(event) => setPriority(event.target.value)}><option value="">All priorities</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select><input value={region} onChange={(event) => setRegion(event.target.value)} placeholder="Filter region" /></div></div><div className="table-wrap"><table><thead><tr><th>Task</th><th>Region / team</th><th>Status</th><th>Due</th><th>Progress</th><th>Risk</th></tr></thead><tbody>{tasks.map((task) => <tr key={task.task_id} onClick={() => setSelectedTask(task)}><td><strong>{task.title}</strong><small>{task.task_id}</small></td><td>{task.region}<small>{task.team}</small></td><td><span className={`badge ${task.status}`}>{task.status.replace("_", " ")}</span></td><td className={task.is_overdue ? "overdue" : ""}>{formatDate(task.due_date)}</td><td><div className="mini-progress"><span style={{ width: `${task.progress_pct}%` }} /></div><small>{task.progress_pct}%</small></td><td><span className={`risk-text ${task.risk_score >= 70 ? "high" : task.risk_score >= 40 ? "medium" : "low"}`}>{Math.round(task.risk_score)}</span></td></tr>)}</tbody></table>{!tasks.length && <EmptyState message="No tasks match the current filters." />}</div></section>
      </main>
    </div>
  );
}

function Metric({ label, value, note, tone = "" }: { label: string; value: number | string; note: string; tone?: string }) { return <div className="metric-card"><span className="metric-label">{label}</span><strong className={tone}>{value}</strong><small>{note}</small></div>; }
function EmptyState({ message = "No task data loaded yet." }: { message?: string }) { return <div className="empty-state"><span>◌</span><p>{message}</p><small>Run the synthetic data generator and loader.</small></div>; }

export default App;
