#!/usr/bin/env python3
"""Reproduce source-bound audit finding: advertised non-grid axes are ignored."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
TASK_ID = "b19fa2726c36"
module, source, digest = load_selected_generator(TASK_ID, root=ROOT)


def grid_sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


pairs = [
    ("anchor_corner", False, True),
    ("asymmetry_force", False, True),
    ("palette_kind", "warm", "cool"),
    ("texture", "warm", "cool"),
]
cases = []
for difficulty, seed, sample_index in (
    ("easy", 0, 3),
    (None, 17, 5),
    ("hard", 29, 7),
):
    for axis, low_value, high_value in pairs:
        low = module.generate(
            seed, sample_index, difficulty=difficulty, **{axis: low_value}
        )
        high = module.generate(
            seed, sample_index, difficulty=difficulty, **{axis: high_value}
        )
        cases.append(
            {
                "difficulty": difficulty,
                "seed": seed,
                "sample_index": sample_index,
                "axis": axis,
                "low_value": low_value,
                "high_value": high_value,
                "identical_outputs": low == high,
                "low_sha256": grid_sha(low),
                "high_sha256": grid_sha(high),
                "shape": [len(low), len(low[0])],
                "self_check_low": module.self_check(low, difficulty=difficulty),
                "self_check_high": module.self_check(high, difficulty=difficulty),
            }
        )

unknown = module.generate(5, 2, difficulty="easy", __audit_typo_axis__="ignored")
result = {
    "schema": "arcpuzzles-review-audit-reproduction-v1",
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": digest,
    "advertised_axes": {name: module.AXES[name] for name, *_ in pairs},
    "cases": cases,
    "unknown_override_accepted": bool(unknown),
    "summary": {
        "comparisons": len(cases),
        "identical_comparisons": sum(c["identical_outputs"] for c in cases),
        "self_check_failures": sum(
            bool(c["self_check_low"] or c["self_check_high"]) for c in cases
        ),
    },
}
out = HERE.with_name("ignored_axes_counterexample.json")
out.write_text(json.dumps(result, indent=2) + "\n")
assert digest == "04ec94fc42cffc4e75c692f94a3b4724507318af4e2eff2b45833e7a72c5d498", result
assert all(c["identical_outputs"] for c in cases), result
assert result["summary"]["self_check_failures"] == 0, result
assert result["unknown_override_accepted"], result
print(out)
