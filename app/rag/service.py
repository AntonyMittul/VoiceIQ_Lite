from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    title: str
    source: str
    section: str
    content: str


@dataclass(frozen=True)
class Retrieval:
    chunk: DocumentChunk
    score: float


@dataclass(frozen=True)
class Answer:
    answer: str
    citations: list[dict[str, str | float]]
    grounded: bool


def chunk_markdown(path: str | Path, max_words: int = 180) -> list[DocumentChunk]:
    source_path = Path(path)
    raw = source_path.read_text(encoding="utf-8")
    title = source_path.stem.replace("_", " ").title()
    section = "Overview"
    chunks: list[DocumentChunk] = []
    buffer: list[str] = []
    chunk_number = 0

    def flush() -> None:
        nonlocal chunk_number
        content = " ".join(buffer).strip()
        if not content:
            return
        words = content.split()
        for offset in range(0, len(words), max_words):
            chunk_number += 1
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{source_path.name}:{chunk_number}",
                    title=title,
                    source=source_path.name,
                    section=section,
                    content=" ".join(words[offset : offset + max_words]),
                )
            )
        buffer.clear()

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            flush()
            section = stripped.lstrip("# ").strip() or "Overview"
        elif stripped:
            buffer.append(stripped.lstrip("- "))
    flush()
    return chunks


class RagIndex:
    def __init__(self, chunks: list[DocumentChunk], min_score: float = 0.12) -> None:
        self.chunks = chunks
        self.min_score = min_score
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([chunk.content for chunk in chunks]) if chunks else None

    @classmethod
    def from_directory(cls, directory: str | Path, min_score: float = 0.12) -> "RagIndex":
        paths = sorted(Path(directory).glob("*.md"))
        chunks = [chunk for path in paths for chunk in chunk_markdown(path)]
        return cls(chunks, min_score)

    def retrieve(self, question: str, top_k: int = 3) -> list[Retrieval]:
        if not self.chunks or self.matrix is None:
            return []
        query = self.vectorizer.transform([question])
        scores = (self.matrix @ query.T).toarray().ravel()
        indexes = np.argsort(scores)[::-1][:top_k]
        return [Retrieval(self.chunks[index], round(float(scores[index]), 4)) for index in indexes]

    def answer(self, question: str, top_k: int = 3) -> Answer:
        results = self.retrieve(question, top_k)
        grounded_results = [result for result in results if result.score >= self.min_score]
        if not grounded_results:
            return Answer(
                answer="Insufficient evidence in the available SOP documents to answer that question.",
                citations=[],
                grounded=False,
            )

        citations = [
            {
                "source": result.chunk.source,
                "section": result.chunk.section,
                "chunk_id": result.chunk.chunk_id,
                "score": result.score,
            }
            for result in grounded_results
        ]
        evidence = " ".join(result.chunk.content for result in grounded_results[:2])
        return Answer(
            answer=f"Based on the documented operating guidance: {evidence}",
            citations=citations,
            grounded=True,
        )

