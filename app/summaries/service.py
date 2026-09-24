from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.db.models import TaskRecord
from app.governance.service import risk_score


@dataclass(frozen=True)
class FocusTask:
    task_id: str
    title: str
    reason: str
    risk_score: float


@dataclass(frozen=True)
class DailySummary:
    report_date: date
    total_tasks: int
    open_tasks: int
    completed_tasks: int
    overdue_tasks: int
    blocked_tasks: int
    high_priority_tasks: int
    focus_tasks: list[FocusTask]
    narrative: str


def build_daily_summary(
    tasks: list[TaskRecord],
    as_of: date | None = None,
    focus_limit: int = 5,
) -> DailySummary:
    report_date = as_of or datetime.now(UTC).date()
    open_tasks = [task for task in tasks if task.status != "completed"]
    overdue_tasks = [task for task in open_tasks if task.due_date < report_date]
    blocked_tasks = [task for task in open_tasks if task.status == "blocked"]
    high_priority_tasks = [
        task for task in open_tasks if task.priority in {"high", "critical"}
    ]
    ranked = sorted(open_tasks, key=lambda task: risk_score(task, report_date), reverse=True)
    focus_tasks = [
        FocusTask(
            task_id=task.task_id,
            title=task.title,
            reason=_focus_reason(task, report_date),
            risk_score=risk_score(task, report_date),
        )
        for task in ranked[:focus_limit]
    ]
    narrative = (
        f"{len(open_tasks)} open task(s), {len(overdue_tasks)} overdue, "
        f"and {len(blocked_tasks)} blocked. "
        f"Start with the highest-risk focus task, confirm its blocker or next action, "
        f"and record the owner follow-up."
    )
    return DailySummary(
        report_date=report_date,
        total_tasks=len(tasks),
        open_tasks=len(open_tasks),
        completed_tasks=len(tasks) - len(open_tasks),
        overdue_tasks=len(overdue_tasks),
        blocked_tasks=len(blocked_tasks),
        high_priority_tasks=len(high_priority_tasks),
        focus_tasks=focus_tasks,
        narrative=narrative,
    )


def _focus_reason(task: TaskRecord, report_date: date) -> str:
    reasons: list[str] = []
    if task.due_date < report_date:
        reasons.append("overdue")
    if task.status == "blocked":
        reasons.append("blocked")
    if task.priority in {"high", "critical"}:
        reasons.append(f"{task.priority} priority")
    if task.previous_delay_count:
        reasons.append(f"{task.previous_delay_count} previous delay(s)")
    return ", ".join(reasons) or "risk score indicates review"

