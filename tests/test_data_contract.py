from datetime import date

import pandas as pd

from app.data.generate import generate_tasks
from app.data.validation import validate_tasks_frame


def test_generator_is_deterministic_and_valid() -> None:
    first = generate_tasks(10, seed=7, as_of=date(2026, 1, 1))
    second = generate_tasks(10, seed=7, as_of=date(2026, 1, 1))
    pd.testing.assert_frame_equal(first, second)
    tasks, report = validate_tasks_frame(first)
    assert len(tasks) == 10
    assert report.is_valid


def test_validation_reports_missing_and_invalid_records() -> None:
    frame = generate_tasks(2, seed=7, as_of=date(2026, 1, 1)).drop(columns=["team"])
    _, report = validate_tasks_frame(frame)
    assert report.missing_columns == ["team"]

