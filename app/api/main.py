from datetime import UTC, date, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.schema import Task
from app.db.models import Approval, AuditEvent, Escalation, TaskRecord
from app.db.session import get_session
from app.governance.service import recommend_escalation
from app.rag.service import RagIndex

app = FastAPI(
    title="VoiceIQ Lite API",
    description="AI operations governance copilot proof of concept",
    version="0.1.0",
)

RAG_INDEX = RagIndex.from_directory(Path(__file__).resolve().parents[2] / "data" / "sops")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "voiceiq-lite-api", "version": app.version}


@app.get("/api/v1/tasks/schema", response_model=dict[str, object], tags=["data"])
def task_schema() -> dict[str, object]:
    return Task.model_json_schema()


class AssistantRequest(BaseModel):
    question: str
    top_k: int = 3


class AssistantResponse(BaseModel):
    answer: str
    grounded: bool
    citations: list[dict[str, str | float]]


class EscalationResponse(BaseModel):
    escalation_id: int | None = None
    task_id: str
    rule_code: str
    reason: str
    evidence: dict[str, object]
    status: str = "recommended"


class DecisionRequest(BaseModel):
    reviewer_id: str
    decision: str
    comment: str | None = None


@app.post("/api/v1/assistant/ask", response_model=AssistantResponse, tags=["assistant"])
def ask_assistant(request: AssistantRequest) -> AssistantResponse:
    result = RAG_INDEX.answer(request.question, top_k=max(1, min(request.top_k, 5)))
    return AssistantResponse(
        answer=result.answer,
        grounded=result.grounded,
        citations=result.citations,
    )


@app.get("/api/v1/escalations/recommendations", response_model=list[EscalationResponse], tags=["governance"])
def escalation_recommendations(session: Session = Depends(get_session)) -> list[EscalationResponse]:  # noqa: B008
    tasks = session.scalars(select(TaskRecord).where(TaskRecord.status != "completed")).all()
    recommendations = []
    for task in tasks:
        recommendation = recommend_escalation(task)
        if recommendation:
            recommendations.append(
                EscalationResponse(
                    task_id=task.task_id,
                    rule_code=recommendation.rule_code,
                    reason=recommendation.reason,
                    evidence=recommendation.evidence,
                )
            )
    return recommendations


@app.post("/api/v1/escalations/{task_id}", response_model=EscalationResponse, tags=["governance"])
def create_escalation(task_id: str, session: Session = Depends(get_session)) -> EscalationResponse:  # noqa: B008
    task = session.get(TaskRecord, task_id)
    if task is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Task not found")
    recommendation = recommend_escalation(task)
    if recommendation is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Task does not meet escalation rules")

    escalation = Escalation(
        task_id=task_id,
        rule_code=recommendation.rule_code,
        reason=recommendation.reason,
        evidence=recommendation.evidence,
        status="pending",
    )
    session.add(escalation)
    session.flush()
    session.add(
        AuditEvent(
            event_type="escalation_recommended",
            actor_id=None,
            entity_type="escalation",
            entity_id=str(escalation.escalation_id),
            payload={"task_id": task_id, "reason": recommendation.reason},
        )
    )
    session.commit()
    return EscalationResponse(
        escalation_id=escalation.escalation_id,
        task_id=task_id,
        rule_code=escalation.rule_code,
        reason=escalation.reason,
        evidence=escalation.evidence or {},
        status=escalation.status,
    )


@app.post("/api/v1/escalations/{escalation_id}/decision", response_model=EscalationResponse, tags=["governance"])
def decide_escalation(
    escalation_id: int,
    request: DecisionRequest,
    session: Session = Depends(get_session),  # noqa: B008
) -> EscalationResponse:
    from fastapi import HTTPException

    if request.decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=422, detail="Decision must be approved or rejected")
    escalation = session.get(Escalation, escalation_id)
    if escalation is None:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if not escalation.reason or not escalation.evidence:
        raise HTTPException(status_code=409, detail="Escalation requires visible reason and evidence")
    if escalation.status != "pending":
        raise HTTPException(status_code=409, detail="Escalation already has a final decision")

    escalation.status = request.decision
    session.add(
        Approval(
            escalation_id=escalation_id,
            reviewer_id=request.reviewer_id,
            decision=request.decision,
            comment=request.comment,
        )
    )
    session.add(
        AuditEvent(
            event_type="escalation_decided",
            actor_id=request.reviewer_id,
            entity_type="escalation",
            entity_id=str(escalation_id),
            payload={"decision": request.decision, "comment": request.comment},
        )
    )
    session.commit()
    return EscalationResponse(
        escalation_id=escalation.escalation_id,
        task_id=escalation.task_id,
        rule_code=escalation.rule_code,
        reason=escalation.reason,
        evidence=escalation.evidence,
        status=escalation.status,
    )


@app.get("/api/v1/audit-events", response_model=list[dict[str, object]], tags=["governance"])
def audit_events(limit: int = Query(default=100, ge=1, le=500), session: Session = Depends(get_session)) -> list[dict[str, object]]:  # noqa: B008
    events = session.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)).all()
    return [
        {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "actor_id": event.actor_id,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "payload": event.payload,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


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
