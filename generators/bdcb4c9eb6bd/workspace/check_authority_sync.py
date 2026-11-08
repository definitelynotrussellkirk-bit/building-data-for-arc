"""Check exact selected/canonical Racket source synchronization for this task."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

TASK = "bdcb4c9eb6bd"
ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "shared/data/base/solutions/training/292dd178__bdcb4c9eb6bd.json"
CANONICAL = ROOT / "shared/data/canonical/puzzles.jsonl"


def canonical_row():
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise ValueError(f"missing canonical task {TASK}")


def normalized_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


def main() -> int:
    row = canonical_row()
    base = json.loads(BASE.read_text())
    canonical = row["program_solution"]
    selected = base["racket_target"]["target_code"]
    report = {
        "task_id": TASK,
        "exact_equal": canonical == selected,
        "canonical_exact_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "selected_exact_sha256": hashlib.sha256(selected.encode()).hexdigest(),
        "canonical_normalized_hash": normalized_hash(canonical),
        "selected_normalized_hash": normalized_hash(selected),
    }
    print(json.dumps(report, indent=2))
    return 0 if report["exact_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
