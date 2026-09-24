import type { DashboardMetrics, Task } from "./types";

const api = async <T,>(path: string): Promise<T> => {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json() as Promise<T>;
};

export const fetchMetrics = () => api<DashboardMetrics>("/api/v1/metrics");

export const fetchTasks = (filters: Record<string, string>) => {
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value));
  return api<Task[]>(`/api/v1/tasks?${query.toString()}`);
};
