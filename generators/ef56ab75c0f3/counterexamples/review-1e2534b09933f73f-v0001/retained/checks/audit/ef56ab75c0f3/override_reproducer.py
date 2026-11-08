from __future__ import annotations

import hashlib
import json
from pathlib import Path

from puzzle_generators import base
from generators.ef56ab75c0f3 import generator

ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = ROOT / "repo" / "generators" / generator.TASK_ID / "generator.py"


def run_case(difficulty: str, requested: int) -> dict:
    captured = []
    base.set_ctx_observer(captured.append)
    try:
        grid = generator.generate(
            123,
            0,
            difficulty=difficulty,
            n_doors=requested,
        )
    finally:
        base.set_ctx_observer(None)
    door_cells = [v for row in grid for v in row if v in (6, 8)]
    ctx = captured[-1]
    return {
        "seed": 123,
        "sample_index": 0,
        "difficulty": difficulty,
        "overrides": {"n_doors": requested},
        "declared_axis": generator.AXES["n_doors"],
        "returned_grid": grid,
        "observed_door_colors": door_cells,
        "observed_n_doors": len(door_cells),
        "expected_n_doors": requested,
        "override_honored": len(door_cells) == requested,
        "self_check_errors": generator.self_check(grid, difficulty=difficulty),
        "ctx_drawn_keys": sorted(ctx._drawn),
        "ctx_recorded_n_doors": ctx._drawn.get("n_doors"),
    }


def main() -> None:
    cases = [run_case("easy", 2), run_case("hard", 1)]
    assert all(case["self_check_errors"] == [] for case in cases)
    assert all(not case["override_honored"] for case in cases)
    report = {
        "schema": "audit_override_reproducer_v1",
        "task_id": generator.TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "generator_version": generator.VERSION,
        "finding": "The advertised exact n_doors override is bypassed by fixed easy/hard branches; self_check does not detect the mismatch.",
        "cases": cases,
        "official_override_gate": {
            "exit_code": 1,
            "summary": "checks/audit-ef56-override/checks/ef56ab75c0f3_after_battery_summary.json",
            "results": "checks/audit-ef56-override/checks/ef56ab75c0f3_after_override_results.json",
            "log": "checks/audit-ef56-override/checks/ef56ab75c0f3_after_override.log",
        },
        "command": ["python3", "../checks/audit/ef56ab75c0f3/override_reproducer.py"],
        "environment": {"PYTHONPATH": ".:shared/runtime"},
        "cwd": "repo",
    }
    out = ROOT / "checks" / "audit" / generator.TASK_ID / "override_reproducer.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
