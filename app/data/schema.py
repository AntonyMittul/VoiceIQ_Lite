from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1, description="Stable unique task identifier")
    title: str = Field(min_length=1)
    region: str = Field(min_length=1)
    team: str = Field(min_length=1)
    assignee: str = Field(min_length=1)
    status: TaskStatus
    priority: TaskPriority
    created_date: date
    due_date: date
    completed_date: date | None = None
    progress_pct: float = Field(ge=0, le=100)
    open_task_count: int = Field(ge=0)
    previous_delay_count: int = Field(ge=0)
    blocker: str | None = None

    @field_validator("completed_date")
    @classmethod
    def completed_date_requires_completion(cls, value: date | None) -> date | None:
        return value

    def is_overdue(self, as_of: date | None = None) -> bool:
        reference_date = as_of or date.today()
        return self.status != TaskStatus.COMPLETED and self.due_date < reference_date


REQUIRED_TASK_COLUMNS = tuple(Task.model_fields)

