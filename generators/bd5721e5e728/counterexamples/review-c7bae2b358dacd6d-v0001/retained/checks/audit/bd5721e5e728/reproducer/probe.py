#!/usr/bin/env python3
"""Reproduce ignored/weakly validated override controls for bd5721e5e728."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from pathlib import Path
from typing import Any

from reviewer_support import load_selected_generator

TASK_ID = "bd5721e5e728"
EXPECTED_SOURCE_SHA256 = "c8c7236b327ac6ede7a67cf6039bf44c55dd0a4f9cf8d502bac10594dff0c047"
SEED = 0
SAMPLE_INDEX = 0
DIFFICULTY = "medium"
REQUESTED_OVERRIDES = {
    "grid_h": 22,
    "grid_w": 24,
    "n_shapes": 4,
    "count": 3,
}


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def component_shapes(grid: list[list[int]]) -> Counter[tuple[tuple[int, int], ...]]:
    h, w = len(grid), len(grid[0])
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    shapes: Counter[tuple[tuple[int, int], ...]] = Counter()
    while pending:
        start = min(pending)
        pending.remove(start)
        q = deque([start])
        cells = []
        while q:
            r, c = q.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in pending:
                    pending.remove(nb)
                    q.append(nb)
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        shape = tuple(sorted((r - r0, c - c0) for r, c in cells))
        shapes[shape] += 1
    return shapes


def observe(grid: list[list[int]], module: Any) -> dict[str, Any]:
    shapes = component_shapes(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "object_count": sum(shapes.values()),
        "n_shapes": len(shapes),
        "shape_instance_counts": sorted(shapes.values()),
        "self_check": module.self_check(grid),
        "grid_sha256": digest(grid),
    }


def attempt(module: Any, overrides: dict[str, Any]) -> dict[str, Any]:
    try:
        grid = module.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY, **overrides)
        return {"accepted": True, "observed": observe(grid, module), "grid": grid}
    except Exception as exc:  # an explicit rejection would be the healthy behavior
        return {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=args.repo.resolve())
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"source hash mismatch: {source_sha256}")

    baseline_grid = module.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY)
    requested_grid = module.generate(
        SEED, SAMPLE_INDEX, difficulty=DIFFICULTY, **REQUESTED_OVERRIDES
    )
    baseline = observe(baseline_grid, module)
    requested = observe(requested_grid, module)

    validation_probes = {
        "unknown_axis": attempt(module, {"unknown_axis": 123}),
        "bool_for_int": attempt(module, {"grid_h": False}),
        "float_for_int": attempt(module, {"grid_h": 22.0}),
        "string_for_int": attempt(module, {"grid_h": "22"}),
    }
    # Keep the report compact: full repeated grids are unnecessary for scalar probes.
    for row in validation_probes.values():
        row.pop("grid", None)

    report = {
        "schema": "arcpuzzles-audit-override-reproducer-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha256,
        "seed": SEED,
        "sample_index": SAMPLE_INDEX,
        "difficulty": DIFFICULTY,
        "requested_overrides": REQUESTED_OVERRIDES,
        "baseline": baseline,
        "requested": requested,
        "exact_grid_equal_to_omission": requested_grid == baseline_grid,
        "requested_dimension_contract_met": (
            requested["grid_h"] == REQUESTED_OVERRIDES["grid_h"]
            and requested["grid_w"] == REQUESTED_OVERRIDES["grid_w"]
        ),
        "requested_shape_contract_met": requested["n_shapes"] == REQUESTED_OVERRIDES["n_shapes"],
        "validation_probes": validation_probes,
        "finding": (
            "Valid exact controls are silently ignored: the combined request returns the exact "
            "same 13x15 grid as omission instead of the requested 22x24 grid. Unknown and "
            "wrongly typed controls are accepted as well."
        ),
        "command": [
            "python3", "../checks/audit/bd5721e5e728/reproducer/probe.py",
            "--repo", ".", "--out", "../checks/audit/bd5721e5e728/reproducer",
        ],
        "cwd": "repo",
    }

    (args.out / "input.json").write_text(json.dumps(requested_grid, indent=2) + "\n")
    (args.out / "baseline-input.json").write_text(json.dumps(baseline_grid, indent=2) + "\n")
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    expected_failure_observed = (
        requested_grid == baseline_grid
        and not report["requested_dimension_contract_met"]
        and all(row["accepted"] for row in validation_probes.values())
        and requested["self_check"] == []
    )
    print(json.dumps({
        "task_id": TASK_ID,
        "generator_sha256": source_sha256,
        "expected_failure_observed": expected_failure_observed,
        "report": str(args.out / "report.json"),
    }, sort_keys=True))
    return 0 if expected_failure_observed else 1


if __name__ == "__main__":
    raise SystemExit(main())
