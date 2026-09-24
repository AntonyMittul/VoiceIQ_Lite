import type { AssistantResponse, DailySummary, DashboardMetrics, Escalation, Task } from "./types";

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

export const fetchSummary = () => api<DailySummary>("/api/v1/summaries/daily");
export const fetchEscalations = () => api<Escalation[]>("/api/v1/escalations/recommendations");
export const askAssistant = (question: string) => fetch("/api/v1/assistant/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) }).then(async (response) => { if (!response.ok) throw new Error("Assistant request failed"); return response.json() as Promise<AssistantResponse>; });
export const createEscalation = (taskId: string) => fetch(`/api/v1/escalations/${taskId}`, { method: "POST" }).then(async (response) => { if (!response.ok) throw new Error((await response.json()).detail ?? "Could not create escalation"); return response.json() as Promise<Escalation>; });
export const decideEscalation = (id: number, decision: "approved" | "rejected") => fetch(`/api/v1/escalations/${id}/decision`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reviewer_id: "local-manager", decision }) }).then(async (response) => { if (!response.ok) throw new Error((await response.json()).detail ?? "Could not record decision"); return response.json() as Promise<Escalation>; });
export const seedDemoData = () => fetch("/api/v1/demo/seed", { method: "POST" }).then(async (response) => { if (!response.ok) throw new Error("Could not load demo data"); return response.json() as Promise<{ loaded: number; total: number }>; });
