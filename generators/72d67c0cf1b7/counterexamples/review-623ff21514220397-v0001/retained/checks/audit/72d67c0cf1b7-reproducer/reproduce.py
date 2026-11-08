"""Compact source-bound reproducer for audit target 72d67c0cf1b7."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "72d67c0cf1b7"
ROOT = find_root(__file__)


def canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def attempt(generator, kwargs):
    try:
        grid = generator.generate(0, 0, **kwargs)
    except Exception as exc:  # reproducer records the public failure verbatim
        return {
            "status": "raised",
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    return {
        "status": "returned",
        "shape": [len(grid), len(grid[0])],
        "distinct_nonzero_colors": len({v for row in grid for v in row if v}),
        "self_check": generator.self_check(grid),
        "grid_sha256": hashlib.sha256(
            json.dumps(grid, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def main() -> int:
    generator, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    program = canonical_program()
    cases = [
        {
            "name": "declared_grid_h_value_rejected_in_easy_band",
            "kwargs": {"difficulty": "easy", "grid_h": 7},
        },
        {
            "name": "declared_n_distinct_colors_ignored",
            "kwargs": {"difficulty": "medium", "n_distinct_colors": 5},
        },
        {
            "name": "advertised_no_motifs_texture_fails_self_check",
            "kwargs": {"difficulty": "medium", "texture": "no_motifs"},
        },
    ]
    for case in cases:
        case["result"] = attempt(generator, case["kwargs"])
    report = {
        "schema": "arc-audit-reproducer-v1",
        "task_id": TASK_ID,
        "generator_path": str(source),
        "generator_sha256": source_sha,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "declared_axes": generator.AXES,
        "cases": cases,
        "command": [
            "python3",
            "review.py",
            "run",
            "python3",
            "../checks/audit/72d67c0cf1b7-reproducer/reproduce.py",
        ],
        "cwd": "packet_root",
    }
    output = Path(__file__).with_name("report.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
