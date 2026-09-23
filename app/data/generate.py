import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


def generate_tasks(count: int = 100, seed: int = 42, as_of: date | None = None) -> pd.DataFrame:
    rng = random.Random(seed)
    today = as_of or date.today()
    regions = ["Hyderabad", "Bengaluru", "Pune", "Chennai"]
    priorities = ["low", "medium", "high", "critical"]
    rows = []
    for number in range(1, count + 1):
        created = today - timedelta(days=rng.randint(3, 45))
        due = created + timedelta(days=rng.randint(3, 20))
        status = rng.choices(["open", "in_progress", "completed", "blocked"], [35, 35, 20, 10])[0]
        progress = 100.0 if status == "completed" else float(rng.randint(0, 95))
        completed = today - timedelta(days=rng.randint(0, 5)) if status == "completed" else None
        rows.append(
            {
                "task_id": f"TSK-{number:04d}",
                "title": f"Operational review {number:04d}",
                "region": rng.choice(regions),
                "team": f"Team-{rng.randint(1, 6)}",
                "assignee": f"Agent-{rng.randint(1, 30):02d}",
                "status": status,
                "priority": rng.choice(priorities),
                "created_date": created,
                "due_date": due,
                "completed_date": completed,
                "progress_pct": progress,
                "open_task_count": rng.randint(0, 12),
                "previous_delay_count": rng.choices([0, 1, 2, 3], [55, 25, 15, 5])[0],
                "blocker": rng.choice([None, None, None, "Awaiting customer response", "Dependency pending"]),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic VoiceIQ task data")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data/generated/tasks.csv"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generate_tasks(args.count, args.seed).to_csv(args.output, index=False)
    print(f"Wrote {args.count} synthetic tasks to {args.output}")


if __name__ == "__main__":
    main()

