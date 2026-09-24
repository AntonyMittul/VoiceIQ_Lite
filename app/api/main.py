from datetime import UTC, date, datetime

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.schema import Task
from app.db.models import TaskRecord
from app.db.session import get_session

app = FastAPI(
    title="VoiceIQ Lite API",
    description="AI operations governance copilot proof of concept",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "voiceiq-lite-api", "version": app.version}


@app.get("/api/v1/tasks/schema", response_model=dict[str, object], tags=["data"])
def task_schema() -> dict[str, object]:
    return Task.model_json_schema()


class TaskListItem(BaseModel):
    task_id: str
    title: str
    region: str
    team: str
    assignee: str
    status: str
    priority: str
    due_date: date
    progress_pct: float
    previous_delay_count: int
    blocker: str | None
    is_overdue: bool
    risk_score: float


class DashboardMetrics(BaseModel):
    total_tasks: int
    overdue_tasks: int
    completed_tasks: int
    completion_rate: float
    high_priority_open_tasks: int
    blocked_tasks: int


def _risk_score(task: TaskRecord, as_of: date) -> float:
    overdue_days = max((as_of - task.due_date).days, 0)
    score = min(
        100.0,
        overdue_days * 12
        + task.previous_delay_count * 12
        + max(0.0, 60.0 - task.progress_pct) * 0.35
        + task.open_task_count * 1.5
        + (15 if task.priority in {"high", "critical"} else 0),
    )
    return round(score, 1)


@app.get("/api/v1/metrics", response_model=DashboardMetrics, tags=["dashboard"])
def dashboard_metrics(session: Session = Depends(get_session)) -> DashboardMetrics:  # noqa: B008
    tasks = session.scalars(select(TaskRecord)).all()
    today = datetime.now(UTC).date()
    completed = sum(task.status == "completed" for task in tasks)
    overdue = sum(task.status != "completed" and task.due_date < today for task in tasks)
    high_priority = sum(
        task.status != "completed" and task.priority in {"high", "critical"} for task in tasks
    )
    blocked = sum(task.status == "blocked" for task in tasks)
    return DashboardMetrics(
        total_tasks=len(tasks),
        overdue_tasks=overdue,
        completed_tasks=completed,
        completion_rate=round(completed / len(tasks) * 100, 1) if tasks else 0.0,
        high_priority_open_tasks=high_priority,
        blocked_tasks=blocked,
    )


@app.get("/api/v1/tasks", response_model=list[TaskListItem], tags=["dashboard"])
def list_tasks(
    status: str | None = Query(default=None),
    region: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),  # noqa: B008
) -> list[TaskListItem]:
    statement = select(TaskRecord).order_by(TaskRecord.due_date.asc()).limit(limit)
    if status:
        statement = statement.where(TaskRecord.status == status)
    if region:
        statement = statement.where(TaskRecord.region == region)
    if priority:
        statement = statement.where(TaskRecord.priority == priority)

    today = datetime.now(UTC).date()
    return [
        TaskListItem(
            task_id=task.task_id,
            title=task.title,
            region=task.region,
            team=task.team,
            assignee=task.assignee,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            progress_pct=task.progress_pct,
            previous_delay_count=task.previous_delay_count,
            blocker=task.blocker,
            is_overdue=task.status != "completed" and task.due_date < today,
            risk_score=_risk_score(task, today),
        )
        for task in session.scalars(statement).all()
    ]
