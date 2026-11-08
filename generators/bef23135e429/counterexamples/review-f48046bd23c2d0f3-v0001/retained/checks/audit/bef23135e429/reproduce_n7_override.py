#!/usr/bin/env python3
"""Reproduce source-bound audit finding: n_7_cells override is ignored."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
TASK_ID = "bef23135e429"
module, source, digest = load_selected_generator(TASK_ID, root=ROOT)


def grid_sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


cases = []
for seed, sample_index, difficulty in (
    (123, 4, None),
    (0, 0, None),
    (77, 3, "hard"),
):
    low = module.generate(
        seed, sample_index, difficulty=difficulty, n_7_cells=2
    )
    high = module.generate(
        seed, sample_index, difficulty=difficulty, n_7_cells=16
    )
    cases.append(
        {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "low_override": 2,
            "high_override": 16,
            "identical_outputs": low == high,
            "realized_7_cells_low": sum(v == 7 for row in low for v in row),
            "realized_7_cells_high": sum(v == 7 for row in high for v in row),
            "low_sha256": grid_sha(low),
            "high_sha256": grid_sha(high),
            "self_check_low": module.self_check(low, difficulty=difficulty),
            "self_check_high": module.self_check(high, difficulty=difficulty),
            "grid": low,
        }
    )

result = {
    "schema": "arcpuzzles-review-audit-reproduction-v1",
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": digest,
    "declared_axis": module.AXES["n_7_cells"],
    "source_draw_label": "n_7",
    "cases": cases,
    "summary": {
        "comparisons": len(cases),
        "identical_comparisons": sum(c["identical_outputs"] for c in cases),
        "observed_above_declared_max": any(
            c["realized_7_cells_low"] > 16 for c in cases
        ),
    },
}
out = HERE.with_name("n7_override_counterexample.json")
out.write_text(json.dumps(result, indent=2) + "\n")
assert digest == "408c239fe734f8912239c7d003fe13c0c8cdaa54a218a8862e39279651c480ae", result
assert all(c["identical_outputs"] for c in cases), result
assert result["summary"]["observed_above_declared_max"], result
assert all(not c["self_check_low"] and not c["self_check_high"] for c in cases), result
print(out)
