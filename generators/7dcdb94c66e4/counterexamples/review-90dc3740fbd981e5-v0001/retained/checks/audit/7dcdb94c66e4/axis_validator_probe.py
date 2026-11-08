#!/usr/bin/env python3
"""Independent audit probe for 7dcdb94c66e4.

Checks whether declared exact axes affect/validate generation and whether the
validator enforces a distinct fully-interior decoy blob.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
SOURCE = REPO / "generators" / "7dcdb94c66e4" / "generator.py"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

spec = importlib.util.spec_from_file_location("audit_7dcdb94c66e4", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SOURCE}")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def digest_grid(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    result: list[set[tuple[int, int]]] = []
    while occupied:
        start = min(occupied)
        occupied.remove(start)
        stack = [start]
        comp = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in occupied:
                    occupied.remove(nxt)
                    comp.add(nxt)
                    stack.append(nxt)
        result.append(comp)
    return result


low = {
    "n_blobs": 2,
    "palette_size": 2,
    "n_distinct_colors": 2,
    "palette_kind": "warm",
}
high = {
    "n_blobs": 5,
    "palette_size": 5,
    "n_distinct_colors": 5,
    "palette_kind": "cool",
}
invalid = {
    "n_blobs": 999,
    "palette_size": -7,
    "n_distinct_colors": "not-an-int",
    "palette_kind": "not-a-declared-palette",
    "texture": "not-a-declared-texture",
}

low_grid = gen.generate(314159, 11, difficulty="medium", **low)
high_grid = gen.generate(314159, 11, difficulty="medium", **high)
invalid_grid = gen.generate(314159, 11, difficulty="medium", **invalid)

# One single connected object touches the border and extends into the interior.
# There is no separate fully-interior blob, despite the documented invariant.
validator_impostor = [
    [1, 0, 0, 0, 0],
    [1, 0, 0, 0, 0],
    [1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
]

report = {
    "schema": "audit-axis-validator-probe-v1",
    "task_id": gen.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "declared_rule_hash": getattr(gen, "RULE_HASH", None),
    "seed": 314159,
    "sample_index": 11,
    "difficulty": "medium",
    "axis_override_cases": {
        "low": low,
        "high": high,
        "invalid": invalid,
    },
    "grid_sha256": {
        "low": digest_grid(low_grid),
        "high": digest_grid(high_grid),
        "invalid": digest_grid(invalid_grid),
    },
    "all_three_grids_identical": low_grid == high_grid == invalid_grid,
    "actual_nonzero_component_count": len(components(low_grid)),
    "validator_impostor": {
        "grid": validator_impostor,
        "component_count": len(components(validator_impostor)),
        "self_check_errors": gen.self_check(validator_impostor),
        "has_distinct_fully_interior_component": False,
    },
    "command": ["python3", "checks/audit/7dcdb94c66e4/axis_validator_probe.py"],
    "cwd": "packet_root",
}

out = HERE.with_name("axis_validator_probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
HERE.with_name("validator_impostor_input.json").write_text(
    json.dumps(validator_impostor, indent=2) + "\n"
)
print(json.dumps(report, indent=2, sort_keys=True))

if not report["all_three_grids_identical"]:
    raise SystemExit("declared ignored-axis witness unexpectedly changed")
if report["validator_impostor"]["self_check_errors"]:
    raise SystemExit("validator unexpectedly rejected the impostor")
