#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "23c3ab5fa55f"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
lesson = json.loads((HERE / "lesson.jsonl").read_text().splitlines()[0])
pairs = list(lesson["train"]) + list(lesson["test"])
inputs = [pair["input"] for pair in pairs]
(HERE / "inputs.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")

cases = [
    ("grid_h_float", {"grid_h": 6.9}),
    ("active_rows_float", {"active_rows": 3.8}),
    ("n_distinct_colors_float", {"n_distinct_colors": 2.9}),
    ("grid_w_string", {"grid_w": "9"}),
    ("unknown_key", {"unrecognized_control": 999}),
]
override_results = []
for name, kwargs in cases:
    try:
        grid = GEN.generate(17, 0, difficulty="medium", **kwargs)
        override_results.append({
            "name": name,
            "supplied": kwargs,
            "status": "accepted",
            "observed": GEN.observe_overrides(grid),
            "self_check_errors": GEN.self_check(grid),
        })
    except Exception as exc:
        override_results.append({
            "name": name,
            "supplied": kwargs,
            "status": "rejected",
            "error_type": type(exc).__name__,
            "error": str(exc),
        })

canonical = canonical_pairs(TASK_ID, root=ROOT)
payload = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "lesson": {
        "seed": lesson["seed"],
        "sample_indices": lesson["sample_indices"],
        "difficulty": "easy",
        "train": len(lesson["train"]),
        "test": len(lesson["test"]),
        "self_check_errors": [GEN.self_check(grid) for grid in inputs],
    },
    "canonical_pairs": len(canonical),
    "override_results": override_results,
}
(HERE / "probe-pre.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps({"generator_sha256": SOURCE_SHA, "lesson_pairs": len(inputs), "override_results": override_results}, sort_keys=True))
