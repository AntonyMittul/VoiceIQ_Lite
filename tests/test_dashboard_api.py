from collections.abc import Generator
from datetime import date

from fastapi.testclient import TestClient

from app.api.main import app
from app.data.generate import generate_tasks
from app.data.load import load_tasks
from app.db.session import create_session_factory


def test_dashboard_metrics_and_filters(tmp_path) -> None:
    csv_path = tmp_path / "tasks.csv"
    db_path = tmp_path / "voiceiq.db"
    generate_tasks(12, seed=12, as_of=date(2026, 1, 1)).to_csv(csv_path, index=False)
    database_url = f"sqlite:///{db_path.as_posix()}"
    load_tasks(csv_path, database_url)
    session_factory = create_session_factory(database_url)

    def override_session() -> Generator:
        with session_factory() as session:
            yield session

    from app.db.session import get_session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        metrics = client.get("/api/v1/metrics")
        tasks = client.get("/api/v1/tasks", params={"region": "Hyderabad"})
        assert metrics.status_code == 200
        assert metrics.json()["total_tasks"] == 12
        assert tasks.status_code == 200
        assert all(task["region"] == "Hyderabad" for task in tasks.json())
    finally:
        app.dependency_overrides.clear()

