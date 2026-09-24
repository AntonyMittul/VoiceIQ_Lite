export type DashboardMetrics = {
  total_tasks: number;
  overdue_tasks: number;
  completed_tasks: number;
  completion_rate: number;
  high_priority_open_tasks: number;
  blocked_tasks: number;
};

export type Task = {
  task_id: string;
  title: string;
  region: string;
  team: string;
  assignee: string;
  status: string;
  priority: string;
  due_date: string;
  progress_pct: number;
  previous_delay_count: number;
  blocker: string | null;
  is_overdue: boolean;
  risk_score: number;
};

export type FocusTask = { task_id: string; title: string; reason: string; risk_score: number };
export type DailySummary = {
  report_date: string;
  total_tasks: number;
  open_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  blocked_tasks: number;
  high_priority_tasks: number;
  focus_tasks: FocusTask[];
  narrative: string;
};
export type Citation = { source: string; section: string; chunk_id: string; score: number };
export type AssistantResponse = { answer: string; grounded: boolean; citations: Citation[] };
export type Escalation = { escalation_id?: number; task_id: string; rule_code: string; reason: string; evidence: Record<string, unknown>; status: string };
