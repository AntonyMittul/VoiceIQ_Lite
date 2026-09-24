from collections.abc import Generator
from datetime import date

from fastapi.testclient import TestClient

from app.api.main import app
from app.data.generate import generate_tasks
from app.data.load import load_tasks
from app.db.session import create_session_factory, get_session


def test_escalation_requires_evidence_and_records_decision(tmp_path) -> None:
    csv_path = tmp_path / "tasks.csv"
    db_path = tmp_path / "voiceiq.db"
    frame = generate_tasks(30, seed=17, as_of=date(2026, 1, 1))
    frame.loc[0, "status"] = "blocked"
    frame.loc[0, "priority"] = "critical"
    frame.loc[0, "previous_delay_count"] = 3
    frame.to_csv(csv_path, index=False)
    database_url = f"sqlite:///{db_path.as_posix()}"
    load_tasks(csv_path, database_url)
    session_factory = create_session_factory(database_url)

    def override_session() -> Generator:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        recommendations = client.get("/api/v1/escalations/recommendations")
        assert recommendations.status_code == 200
        task_id = recommendations.json()[0]["task_id"]
        created = client.post(f"/api/v1/escalations/{task_id}")
        assert created.status_code == 200
        escalation_id = created.json()["escalation_id"]
        decision = client.post(
            f"/api/v1/escalations/{escalation_id}/decision",
            json={"reviewer_id": "manager-1", "decision": "approved", "comment": "Confirmed blocker with team."},
        )
        assert decision.status_code == 200
        assert decision.json()["status"] == "approved"
        events = client.get("/api/v1/audit-events")
        assert len(events.json()) == 2
    finally:
        app.dependency_overrides.clear()
