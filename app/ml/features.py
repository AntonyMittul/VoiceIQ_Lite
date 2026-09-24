from datetime import UTC, date, datetime

import pandas as pd

FEATURE_COLUMNS = [
    "days_until_due",
    "progress_pct",
    "open_task_count",
    "previous_delay_count",
    "priority_score",
    "status_score",
    "has_blocker",
]
PRIORITY_SCORE = {"low": 0, "medium": 1, "high": 2, "critical": 3}
STATUS_SCORE = {"completed": 0, "open": 1, "in_progress": 2, "blocked": 3}


def build_features(frame: pd.DataFrame, as_of: date | None = None) -> pd.DataFrame:
    reference_date = as_of or datetime.now(UTC).date()
    data = frame.copy()
    data["created_date"] = pd.to_datetime(data["created_date"]).dt.date
    data["due_date"] = pd.to_datetime(data["due_date"]).dt.date
    data["completed_date"] = pd.to_datetime(data["completed_date"], errors="coerce").dt.date
    data["days_until_due"] = data["due_date"].map(lambda value: (value - reference_date).days)
    data["priority_score"] = data["priority"].map(PRIORITY_SCORE).fillna(0)
    data["status_score"] = data["status"].map(STATUS_SCORE).fillna(0)
    data["has_blocker"] = data["blocker"].notna().astype(int)
    return data


def add_delay_label(frame: pd.DataFrame, as_of: date | None = None) -> pd.DataFrame:
    data = build_features(frame, as_of)
    reference_date = as_of or datetime.now(UTC).date()
    completed_late = data["completed_date"].notna() & (data["completed_date"] > data["due_date"])
    still_open_late = data["completed_date"].isna() & (data["due_date"] < reference_date)
    data["delayed_label"] = (completed_late | still_open_late).astype(int)
    return data

