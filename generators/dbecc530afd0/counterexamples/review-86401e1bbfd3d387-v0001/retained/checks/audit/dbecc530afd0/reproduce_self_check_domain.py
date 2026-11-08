#!/usr/bin/env python3
"""Reproduce source-bound audit finding: self_check admits 3 rectangles."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
TASK_ID = "dbecc530afd0"
module, source, digest = load_selected_generator(TASK_ID, root=ROOT)

grid = [[0 for _ in range(18)] for _ in range(18)]
rectangles = [(1, 3, 1, 3), (6, 8, 6, 8), (11, 13, 11, 13)]
for r1, r2, c1, c2 in rectangles:
    for r, c in ((r1, c1), (r1, c2), (r2, c1), (r2, c2)):
        grid[r][c] = 4

result = {
    "schema": "arcpuzzles-review-audit-reproduction-v1",
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": digest,
    "declared_n_rects_valid": module.AXES["n_rects"]["valid"],
    "constructed_rectangles": rectangles,
    "self_check_errors": module.self_check(grid),
    "observed_overrides": module.observe_overrides(grid),
    "input_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
    "input": grid,
}
out = HERE.with_name("self_check_domain_counterexample.json")
out.write_text(json.dumps(result, indent=2) + "\n")
assert result["self_check_errors"] == [], result
assert result["observed_overrides"]["n_rects"] == 3, result
assert result["declared_n_rects_valid"] == "1..2", result
print(out)
