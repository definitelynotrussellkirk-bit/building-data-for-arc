#!/usr/bin/env python3
"""Reproduce the ignored exact ``k_count=0`` override for task 113148619988."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
RUNTIME = REPO / "shared/runtime"
sys.path.insert(0, str(RUNTIME))

TASK_ID = "113148619988"
EXPECTED_GENERATOR_SHA256 = (
    "170a096bd9ee211b14e2ebb56d03439669c1fbbc628bf7063c46960f07f5daf9"
)
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(
        f"audit_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    generator_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    if generator_sha != EXPECTED_GENERATOR_SHA256:
        raise RuntimeError(
            "audited generator drifted: "
            f"expected {EXPECTED_GENERATOR_SHA256}, got {generator_sha}"
        )

    generator = load_generator()
    case = {
        "seed": 37,
        "sample_index": 0,
        "difficulty": None,
        "overrides": {"k_count": 0},
    }
    grid = generator.generate(
        case["seed"],
        case["sample_index"],
        difficulty=case["difficulty"],
        **case["overrides"],
    )
    counterfactual = [row[:] for row in grid]
    counterfactual[0] = [0] * len(counterfactual[0])
    observed_k = sum(value == 1 for value in grid[0])
    observed_orbit_cells = sum(
        value not in (0, 9) for row in grid[1:] for value in row
    )
    record = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "case": case,
        "observed": {
            "grid_h": len(grid),
            "grid_w": len(grid[0]),
            "k_count": observed_k,
            "n_orbit_cells": observed_orbit_cells,
        },
        "self_check": generator.self_check(grid),
        "input": grid,
        "counterfactual_input_if_k_count_zero_were_honored": counterfactual,
        "finding": (
            "Declared exact k_count=0 is ignored; returned row 0 contains "
            f"{observed_k} color-1 counters."
        ),
        "generation_command": (
            "PYTHONPATH=repo/shared/runtime python3 "
            "checks/audit/113148619988/build_counterexample.py"
        ),
    }
    if record["self_check"]:
        raise RuntimeError(f"counterexample is outside validator domain: {record['self_check']}")
    if observed_k == 0:
        raise RuntimeError("override was unexpectedly honored")

    (HERE / "input.json").write_text(
        json.dumps([grid, counterfactual], indent=2) + "\n"
    )
    (HERE / "override-counterexample.pre-racket.json").write_text(
        json.dumps(record, indent=2) + "\n"
    )
    print(HERE / "override-counterexample.pre-racket.json")


if __name__ == "__main__":
    main()
