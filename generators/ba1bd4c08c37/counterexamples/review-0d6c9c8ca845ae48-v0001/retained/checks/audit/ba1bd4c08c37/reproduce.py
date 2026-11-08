from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "ba1bd4c08c37"
ROOT = Path.cwd()
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

cases = [
    ("seed_bool", True, 0),
    ("seed_float", 1.75, 0),
    ("seed_string", "1", 0),
    ("index_bool", 991, True),
    ("index_float", 991, 1.75),
    ("index_string", 991, "1"),
    ("index_negative", 991, -1),
]
records = []
for name, seed, sample_index in cases:
    try:
        grid = GEN.generate(seed, sample_index, difficulty="medium")
        records.append(
            {
                "case": name,
                "accepted": True,
                "shape": [len(grid), len(grid[0])],
                "grid_sha256": hashlib.sha256(
                    json.dumps(grid, separators=(",", ":")).encode()
                ).hexdigest(),
                "self_check": GEN.self_check(grid, difficulty="medium"),
            }
        )
    except Exception as exc:
        records.append(
            {
                "case": name,
                "accepted": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )

schedule_cases = []
for value in (True, 1.75, "1", -1):
    try:
        result = GEN.schedule_profile(991, value, "medium")
        schedule_cases.append(
            {"sample_index": repr(value), "accepted": True, "profile": result}
        )
    except Exception as exc:
        schedule_cases.append(
            {
                "sample_index": repr(value),
                "accepted": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )

report = {
    "task_id": TASK_ID,
    "generator_path": str(SOURCE_PATH.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "finding": "public seed/sample_index controls and schedule helper accept invalid scalars",
    "generate_cases": records,
    "schedule_cases": schedule_cases,
}
print(json.dumps(report, indent=2, sort_keys=True))
