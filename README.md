# VoiceIQ Lite

AI operations governance copilot proof of concept.

## Current slice

- FastAPI service with `/health` and task schema endpoints.
- Pydantic task contract with strict fields and business enums.
- Deterministic synthetic task generator.
- CSV validation with missing-column, duplicate-ID, and record-level error reporting.
- SQLAlchemy schema for tasks, predictions, documents, conversations, escalations, approvals, and audit events.
- Idempotent CSV loader that validates records before inserting or updating tasks.
- Rule-based delay baseline and time-split logistic regression risk model with metrics and explanations.
- Fictional SOP RAG assistant with section-aware retrieval, citations, and insufficient-evidence refusal.
- Deterministic escalation recommendations with evidence, approval decisions, and audit events.
- Daily manager summary endpoint with prioritized focus tasks and explicit next-action guidance.
- Docker Compose scaffold for the API and PostgreSQL.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
Copy-Item .env.example .env
py -m app.data.generate --count 100
py -m app.data.load data/generated/tasks.csv --database-url sqlite:///voiceiq.db
py -m app.ml.train data/generated/tasks.csv
py -m app.rag.ingest data/sops "When should a task receive manager review?"
curl http://localhost:8000/api/v1/summaries/daily
pytest
uvicorn app.api.main:app --reload
```

Then open `http://localhost:8000/docs` or `http://localhost:8000/health`.

## Run the dashboard

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. To populate the dashboard locally, run the API and then load generated data into `voiceiq.db`:

```powershell
py -m app.data.generate --count 100
py -m app.data.load data/generated/tasks.csv --database-url sqlite:///voiceiq.db
```

## Run with Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

All data in this proof of concept is synthetic. Do not upload real employee or customer data.
