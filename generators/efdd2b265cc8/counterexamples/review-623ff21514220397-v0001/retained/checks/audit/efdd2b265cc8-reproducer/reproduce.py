"""Compact source-bound strict-scalar reproducer for efdd2b265cc8."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "efdd2b265cc8"
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


def attempt(generator, seed, sample_index):
    try:
        grid = generator.generate(seed, sample_index, difficulty="medium")
    except Exception as exc:
        return {
            "status": "raised",
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    return {
        "status": "accepted_invalid_scalar",
        "shape": [len(grid), len(grid[0])],
        "grid_sha256": hashlib.sha256(
            json.dumps(grid, separators=(",", ":")).encode()
        ).hexdigest(),
        "self_check": generator.self_check(grid),
    }


def main() -> int:
    generator, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    program = canonical_program()
    probes = [
        {"seed": True, "sample_index": 0},
        {"seed": 1.75, "sample_index": 0},
        {"seed": "1", "sample_index": 0},
        {"seed": 991, "sample_index": True},
        {"seed": 991, "sample_index": 1.75},
        {"seed": 991, "sample_index": "1"},
        {"seed": 991, "sample_index": -1},
    ]
    for probe in probes:
        probe["result"] = attempt(
            generator, probe["seed"], probe["sample_index"]
        )
    report = {
        "schema": "arc-audit-reproducer-v1",
        "task_id": TASK_ID,
        "generator_path": str(source),
        "generator_sha256": source_sha,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "probes": probes,
        "command": [
            "python3",
            "review.py",
            "run",
            "python3",
            "../checks/audit/efdd2b265cc8-reproducer/reproduce.py",
        ],
        "cwd": "packet_root",
    }
    output = Path(__file__).with_name("report.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
