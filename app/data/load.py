import argparse
from pathlib import Path

from sqlalchemy import select

from app.data.validation import validate_tasks_csv
from app.db.models import TaskRecord
from app.db.session import create_session_factory


def load_tasks(input_path: str | Path, database_url: str | None = None) -> int:
    tasks, report = validate_tasks_csv(input_path)
    if not report.is_valid:
        raise ValueError(
            f"Task file failed validation: {report.invalid_records} invalid records, "
            f"missing columns={report.missing_columns}, duplicates={report.duplicate_task_ids}"
        )

    session_factory = create_session_factory(database_url)
    with session_factory.begin() as session:
        for task in tasks:
            existing = session.scalar(select(TaskRecord).where(TaskRecord.task_id == task.task_id))
            values = task.model_dump(mode="python")
            if existing is None:
                session.add(TaskRecord(**values))
            else:
                for field, value in values.items():
                    setattr(existing, field, value)
    return len(tasks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and load VoiceIQ task CSV data")
    parser.add_argument("input", type=Path)
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    count = load_tasks(args.input, args.database_url)
    print(f"Loaded {count} valid tasks")


if __name__ == "__main__":
    main()

