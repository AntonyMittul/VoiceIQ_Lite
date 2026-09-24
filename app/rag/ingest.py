import argparse
from pathlib import Path

from app.rag.service import RagIndex


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect fictional SOP retrieval coverage")
    parser.add_argument("directory", type=Path, default=Path("data/sops"), nargs="?")
    parser.add_argument("question")
    args = parser.parse_args()
    index = RagIndex.from_directory(args.directory)
    answer = index.answer(args.question)
    print(answer.answer)
    for citation in answer.citations:
        print(f"[{citation['source']} / {citation['section']}] score={citation['score']}")


if __name__ == "__main__":
    main()

