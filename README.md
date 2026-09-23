# VoiceIQ Lite

AI operations governance copilot proof of concept.

## Current slice

- FastAPI service with `/health` and task schema endpoints.
- Pydantic task contract with strict fields and business enums.
- Deterministic synthetic task generator.
- CSV validation with missing-column, duplicate-ID, and record-level error reporting.
- Docker Compose scaffold for the API and PostgreSQL.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
Copy-Item .env.example .env
py -m app.data.generate --count 100
pytest
uvicorn app.api.main:app --reload
```

Then open `http://localhost:8000/docs` or `http://localhost:8000/health`.

## Run with Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

All data in this proof of concept is synthetic. Do not upload real employee or customer data.
