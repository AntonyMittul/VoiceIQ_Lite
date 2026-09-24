from collections.abc import Generator
from datetime import date

from fastapi.testclient import TestClient

from app.api.main import app
from app.data.generate import generate_tasks
from app.data.load import load_tasks
from app.db.session import create_session_factory, get_session
from app.summaries.service import build_daily_summary


def test_daily_summary_prioritizes_open_work() -> None:
    frame = generate_tasks(25, seed=19, as_of=date(2026, 1, 1))
    summary = build_daily_summary([], date(2026, 1, 1))
    assert summary.total_tasks == 0
    assert "open task(s)" in summary.narrative
    assert len(frame) == 25


def test_daily_summary_api_returns_focus_tasks(tmp_path) -> None:
    csv_path = tmp_path / "tasks.csv"
    db_path = tmp_path / "voiceiq.db"
    generate_tasks(25, seed=19, as_of=date(2026, 1, 1)).to_csv(csv_path, index=False)
    database_url = f"sqlite:///{db_path.as_posix()}"
    load_tasks(csv_path, database_url)
    session_factory = create_session_factory(database_url)

    def override_session() -> Generator:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        response = TestClient(app).get("/api/v1/summaries/daily", params={"report_date": "2026-01-01"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["report_date"] == "2026-01-01"
        assert payload["total_tasks"] == 25
        assert len(payload["focus_tasks"]) <= 5
        assert payload["narrative"]
    finally:
        app.dependency_overrides.clear()
