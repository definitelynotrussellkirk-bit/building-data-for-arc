from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "260f488cb5a8"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
CASES = [
    {"name": "float_height", "overrides": {"grid_h": 4.9}},
    {"name": "numeric_string_width", "overrides": {"grid_w": "8"}},
    {"name": "float_width", "overrides": {"grid_w": 8.7}},
]
results = []
for case in CASES:
    grid = GEN.generate(1, 2, difficulty="medium", **case["overrides"])
    observed = GEN.observe_overrides(grid)
    requested_name, requested_value = next(iter(case["overrides"].items()))
    results.append({
        **case,
        "requested_type": type(requested_value).__name__,
        "observed": observed,
        "self_check": GEN.self_check(grid),
        "literal_round_trip": observed[requested_name] == requested_value and type(observed[requested_name]) is type(requested_value),
        "shape": [len(grid), len(grid[0])],
    })
assert all(item["self_check"] == [] for item in results)
assert all(not item["literal_round_trip"] for item in results)
print(json.dumps({
    "schema": "audit-exact-override-coercion-v2",
    "task_id": TASK,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "seed": 1,
    "sample_index": 2,
    "difficulty": "medium",
    "axis_declarations": {name: GEN.AXES[name] for name in ("grid_h", "grid_w")},
    "results": results,
}, indent=2))
