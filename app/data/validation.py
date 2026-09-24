from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from app.data.schema import REQUIRED_TASK_COLUMNS, Task


@dataclass
class ValidationReport:
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_task_ids: list[str] = field(default_factory=list)
    missing_columns: list[str] = field(default_factory=list)
    errors: list[dict[str, object]] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.missing_columns and self.invalid_records == 0 and not self.duplicate_task_ids


def validate_tasks_frame(frame: pd.DataFrame) -> tuple[list[Task], ValidationReport]:
    missing_columns = [column for column in REQUIRED_TASK_COLUMNS if column not in frame.columns]
    if missing_columns:
        report = ValidationReport(len(frame), 0, len(frame), missing_columns=missing_columns)
        return [], report

    duplicate_ids = sorted(frame.loc[frame["task_id"].duplicated(keep=False), "task_id"].astype(str).unique())
    valid_tasks: list[Task] = []
    errors: list[dict[str, object]] = []
    for index, row in frame.iterrows():
        try:
            clean_row = row.where(pd.notna(row), None).to_dict()
            valid_tasks.append(Task.model_validate(clean_row))
        except ValidationError as exc:
            errors.append({"row": int(index), "errors": exc.errors(include_url=False)})

    invalid_records = len(frame) - len(valid_tasks)
    return valid_tasks, ValidationReport(
        total_records=len(frame),
        valid_records=len(valid_tasks),
        invalid_records=invalid_records,
        duplicate_task_ids=duplicate_ids,
        errors=errors,
    )


def validate_tasks_csv(path: str | Path) -> tuple[list[Task], ValidationReport]:
    return validate_tasks_frame(pd.read_csv(path))
