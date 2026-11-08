#!/usr/bin/env python3
"""Reproduce source-bound audit finding: n_7_cells override is ignored."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
TASK_ID = "bef23135e429"
module, source, digest = load_selected_generator(TASK_ID, root=ROOT)

cases = []
for seed, sample_index in ((123, 4), (0, 0), (77, 3)):
    low = module.generate(seed, sample_index, n_7_cells=2)
    high = module.generate(seed, sample_index, n_7_cells=16)
    cases.append({
        "seed": seed,
        "sample_index": sample_index,
        "low_override": 2,
        "high_override": 16,
        "identical_outputs": low == high,
        "realized_7_cells_low": sum(v == 7 for row in low for v in row),
        "realized_7_cells_high": sum(v == 7 for row in high for v in row),
        "low_sha256": hashlib.sha256(json.dumps(low, separators=(",", ":")).encode()).hexdigest(),
        "high_sha256": hashlib.sha256(json.dumps(high, separators=(",", ":")).encode()).hexdigest(),
        "grid": low,
    })
result = {
    "schema": "arcpuzzles-review-audit-reproduction-v1",
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": digest,
    "declared_axis": module.AXES["n_7_cells"],
    "source_draw_label": "n_7",
    "cases": cases,
}
out = HERE.with_name("n7_override_counterexample.json")
out.write_text(json.dumps(result, indent=2) + "\n")
assert all(c["identical_outputs"] for c in cases), result
assert any(c["realized_7_cells_low"] > 16 for c in cases), result
print(out)
