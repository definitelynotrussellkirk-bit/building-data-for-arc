from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "a631936f7715"
ROOT = find_root(__file__)
MODULE, MODULE_PATH, MODULE_SHA256 = load_selected_generator(TASK, root=ROOT)


def frozen(grid):
    return tuple(tuple(row) for row in grid)


rows = []
for band in ("easy", "medium", "hard"):
    for seed in range(5):
        for axis in ("palette_kind", "texture"):
            invalid = MODULE.generate(seed, 0, difficulty=band, **{axis: "typo"})
            broad = MODULE.generate(seed, 0, difficulty=band, **{axis: "broad"})
            rows.append({
                "band": band,
                "seed": seed,
                "axis": axis,
                "invalid_value": "typo",
                "invalid_self_check": MODULE.self_check(invalid),
                "invalid_equals_broad_control": frozen(invalid) == frozen(broad),
            })

representative = MODULE.generate(9, 0, difficulty="easy", palette_kind="typo")
report = {
    "schema": "arc-review-audit-probe-v1",
    "task_id": TASK,
    "generator_path": str(MODULE_PATH.relative_to(ROOT)),
    "generator_sha256": MODULE_SHA256,
    "rule_hash": MODULE.RULE_HASH,
    "axes": MODULE.AXES,
    "bounds": {"bands": ["easy", "medium", "hard"], "seeds": [0, 4], "sample_index": 0, "invalid_axes": ["palette_kind", "texture"]},
    "summary": {
        "invalid_cases": len(rows),
        "accepted": len(rows),
        "self_check_clean": sum(not r["invalid_self_check"] for r in rows),
        "identical_to_broad_control": sum(r["invalid_equals_broad_control"] for r in rows),
    },
    "representative": {
        "seed": 9,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"palette_kind": "typo"},
        "self_check": MODULE.self_check(representative),
        "input": representative,
    },
    "cases": rows,
}
out = Path(__file__).with_name("probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
Path(__file__).with_name("input.json").write_text(json.dumps([representative], indent=2) + "\n")
print(json.dumps(report["summary"], sort_keys=True))
