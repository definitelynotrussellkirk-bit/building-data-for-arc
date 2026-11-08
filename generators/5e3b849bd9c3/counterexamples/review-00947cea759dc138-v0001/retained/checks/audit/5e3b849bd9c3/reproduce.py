#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "5e3b849bd9c3"
SEED = 0
SAMPLE_INDEX = 1
OVERRIDES = {"grid_h": 8, "grid_w": 8, "n_rings": 4}
DELTAS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def exact_ring_centers(grid):
    h, w = len(grid), len(grid[0])
    return [
        [r, c]
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 0
        and all(grid[r + dr][c + dc] == 4 for dr, dc in DELTAS)
    ]


def expected_output(grid):
    out = [row[:] for row in grid]
    for r, c in exact_ring_centers(grid):
        out[r][c] = 8
    return out


def main():
    here = Path(__file__).resolve()
    repo = find_root(here)
    module, source, source_sha256 = load_selected_generator(TASK_ID, root=repo)
    grid = module.generate(SEED, SAMPLE_INDEX, **OVERRIDES)
    centers = exact_ring_centers(grid)
    self_check_errors = module.self_check(grid)
    expected = expected_output(grid)
    report = {
        "schema": "audit-reproduction/1",
        "finding_id": "5e3-ring-count-underfill",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(repo)),
        "generator_sha256": source_sha256,
        "generator_version": module.VERSION,
        "seed": SEED,
        "sample_index": SAMPLE_INDEX,
        "overrides": OVERRIDES,
        "axis_contract": module.AXES["n_rings"],
        "summary_claim": module.SUMMARY,
        "input": grid,
        "input_sha256": digest(grid),
        "requested_ring_count": OVERRIDES["n_rings"],
        "observed_exact_ring_centers": centers,
        "observed_ring_count": len(centers),
        "yellow_cell_count": sum(value == 4 for row in grid for value in row),
        "self_check_errors": self_check_errors,
        "self_check_passed": not self_check_errors,
        "expected_authority_output": expected,
        "expected_authority_output_sha256": digest(expected),
        "finding_reproduced": len(centers) != OVERRIDES["n_rings"] and not self_check_errors,
    }
    target = here.parent
    (target / "input.json").write_text(json.dumps([grid], indent=2) + "\n")
    (target / "counterexample.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha256,
        "requested_ring_count": OVERRIDES["n_rings"],
        "observed_ring_count": len(centers),
        "observed_exact_ring_centers": centers,
        "self_check_errors": self_check_errors,
        "finding_reproduced": report["finding_reproduced"],
    }, indent=2))
    return 0 if report["finding_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
