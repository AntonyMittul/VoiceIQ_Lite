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
