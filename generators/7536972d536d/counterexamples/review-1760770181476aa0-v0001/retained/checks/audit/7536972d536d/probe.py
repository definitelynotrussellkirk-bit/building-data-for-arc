from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "7536972d536d"
ROOT = find_root(__file__)
MODULE, MODULE_PATH, MODULE_SHA256 = load_selected_generator(TASK, root=ROOT)


def frozen(grid):
    return tuple(tuple(row) for row in grid)


rows = []
for band in ("easy", "medium", "hard"):
    for seed in range(10):
        invalid_orientation = MODULE.generate(seed, 0, difficulty=band, orientation="diagonal")
        col_control = MODULE.generate(seed, 0, difficulty=band, orientation="col")
        warm = MODULE.generate(seed, 0, difficulty=band, palette_kind="warm")
        cool = MODULE.generate(seed, 0, difficulty=band, palette_kind="cool")
        size_one = MODULE.generate(seed, 0, difficulty=band, palette_size=1)
        size_eight = MODULE.generate(seed, 0, difficulty=band, palette_size=8)
        unknown = MODULE.generate(seed, 0, difficulty=band, __unknown_axis__="typo")
        baseline = MODULE.generate(seed, 0, difficulty=band)
        rows.append({
            "band": band,
            "seed": seed,
            "invalid_orientation_equals_col": frozen(invalid_orientation) == frozen(col_control),
            "invalid_orientation_self_check": MODULE.self_check(invalid_orientation),
            "warm_equals_cool": frozen(warm) == frozen(cool),
            "palette_size_1_equals_8": frozen(size_one) == frozen(size_eight),
            "unknown_equals_baseline": frozen(unknown) == frozen(baseline),
        })

representative = MODULE.generate(3, 0, difficulty="easy", orientation="diagonal")
report = {
    "schema": "arc-review-audit-probe-v1",
    "task_id": TASK,
    "generator_path": str(MODULE_PATH.relative_to(ROOT)),
    "generator_sha256": MODULE_SHA256,
    "axes": MODULE.AXES,
    "bounds": {"bands": ["easy", "medium", "hard"], "seeds": [0, 9], "sample_index": 0},
    "summary": {
        "cases": len(rows),
        "invalid_orientation_accepted": len(rows),
        "invalid_orientation_equals_col": sum(r["invalid_orientation_equals_col"] for r in rows),
        "invalid_orientation_self_check_clean": sum(not r["invalid_orientation_self_check"] for r in rows),
        "warm_equals_cool": sum(r["warm_equals_cool"] for r in rows),
        "palette_size_1_equals_8": sum(r["palette_size_1_equals_8"] for r in rows),
        "unknown_key_accepted_and_equals_baseline": sum(r["unknown_equals_baseline"] for r in rows),
    },
    "representative": {
        "seed": 3,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"orientation": "diagonal"},
        "self_check": MODULE.self_check(representative),
        "input": representative,
    },
    "cases": rows,
}
out = Path(__file__).with_name("probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
Path(__file__).with_name("input.json").write_text(json.dumps([representative], indent=2) + "\n")
print(json.dumps(report["summary"], sort_keys=True))
