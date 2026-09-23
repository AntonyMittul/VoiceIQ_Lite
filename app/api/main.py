from fastapi import FastAPI

from app.data.schema import Task

app = FastAPI(
    title="VoiceIQ Lite API",
    description="AI operations governance copilot proof of concept",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "voiceiq-lite-api", "version": app.version}


@app.get("/api/v1/tasks/schema", response_model=dict[str, object], tags=["data"])
def task_schema() -> dict[str, object]:
    return Task.model_json_schema()

