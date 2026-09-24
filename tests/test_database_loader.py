from datetime import date

from sqlalchemy import select

from app.data.generate import generate_tasks
from app.data.load import load_tasks
from app.db.models import TaskRecord
from app.db.session import create_session_factory


def test_loader_creates_schema_and_upserts_tasks(tmp_path) -> None:
    csv_path = tmp_path / "tasks.csv"
    db_path = tmp_path / "voiceiq.db"
    generate_tasks(5, seed=11, as_of=date(2026, 1, 1)).to_csv(csv_path, index=False)
    database_url = f"sqlite:///{db_path.as_posix()}"

    assert load_tasks(csv_path, database_url) == 5
    assert load_tasks(csv_path, database_url) == 5

    session_factory = create_session_factory(database_url)
    with session_factory() as session:
        tasks = session.scalars(select(TaskRecord)).all()
        assert len(tasks) == 5
        assert {task.task_id for task in tasks} == {f"TSK-{n:04d}" for n in range(1, 6)}

