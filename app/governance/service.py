from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.db.models import TaskRecord


@dataclass(frozen=True)
class EscalationRecommendation:
    rule_code: str
    reason: str
    evidence: dict[str, object]


def risk_score(task: TaskRecord, as_of: date | None = None) -> float:
    reference_date = as_of or datetime.now(UTC).date()
    overdue_days = max((reference_date - task.due_date).days, 0)
    return round(
        min(
            100.0,
            overdue_days * 12
            + task.previous_delay_count * 12
            + max(0.0, 60.0 - task.progress_pct) * 0.35
            + task.open_task_count * 1.5
            + (15 if task.priority in {"high", "critical"} else 0),
        ),
        1,
    )


def recommend_escalation(task: TaskRecord, as_of: date | None = None) -> EscalationRecommendation | None:
    reference_date = as_of or datetime.now(UTC).date()
    overdue_days = max((reference_date - task.due_date).days, 0)
    score = risk_score(task, reference_date)
    triggers: list[str] = []
    if overdue_days > 0:
        triggers.append(f"overdue by {overdue_days} day(s)")
    if task.status == "blocked":
        triggers.append("task is blocked")
    if task.priority == "critical":
        triggers.append("critical priority")
    if task.previous_delay_count >= 2:
        triggers.append(f"{task.previous_delay_count} previous delays")
    if score < 70 or not triggers or task.status == "completed":
        return None

    evidence = {
        "task_id": task.task_id,
        "risk_score": score,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat(),
        "progress_pct": task.progress_pct,
        "previous_delay_count": task.previous_delay_count,
        "blocker": task.blocker,
        "triggers": triggers,
    }
    return EscalationRecommendation(
        rule_code="TASK_REVIEW_V1",
        reason="Escalation recommended because " + ", ".join(triggers) + ".",
        evidence=evidence,
    )

