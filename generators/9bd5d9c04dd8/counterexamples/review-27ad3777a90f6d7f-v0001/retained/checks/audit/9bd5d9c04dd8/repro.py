"""Source-bound reproduction of invalid sample_index acceptance (audit only)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "9bd5d9c04dd8"
VALUES = [True, False, 1.0, -1]


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main():
    repo = Path.cwd().resolve()
    gen, source, source_sha = load_selected_generator(TASK_ID, root=repo)
    cases = []
    for value in VALUES:
        try:
            grid = gen.generate(731, value, difficulty="easy")
            cases.append({
                "value": value,
                "value_type": type(value).__name__,
                "status": "accepted_invalid_scalar",
                "grid_sha256": grid_hash(grid),
                "self_check_errors": gen.self_check(grid),
                "observed_axes": gen.observe_overrides(grid),
            })
        except Exception as exc:
            cases.append({
                "value": value,
                "value_type": type(value).__name__,
                "status": "rejected",
                "error": f"{type(exc).__name__}: {exc}",
            })
    report = {
        "schema": "audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(repo)),
        "generator_sha256": source_sha,
        "seed": 731,
        "difficulty": "easy",
        "cases": cases,
        "finding": "generate accepts bool, float, and negative sample_index values instead of requiring a nonnegative Python int.",
    }
    out = Path(__file__).resolve().parent / "summary.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
