from pathlib import Path

from app.rag.service import RagIndex, chunk_markdown

SOPS = Path(__file__).resolve().parents[1] / "data" / "sops"


def test_markdown_ingestion_preserves_sections() -> None:
    path = SOPS / "task_escalation_policy.md"
    chunks = chunk_markdown(path)
    assert chunks
    assert any(chunk.section == "High-risk task criteria" for chunk in chunks)


def test_rag_returns_citations_for_grounded_question() -> None:
    index = RagIndex.from_directory(SOPS)
    answer = index.answer("When should a task receive manager review?")
    assert answer.grounded
    assert answer.citations
    assert "previous delays" in answer.answer


def test_rag_refuses_unsupported_question() -> None:
    index = RagIndex.from_directory(SOPS)
    answer = index.answer("What is the weather on Mars today?")
    assert not answer.grounded
    assert answer.citations == []
    assert "Insufficient evidence" in answer.answer
