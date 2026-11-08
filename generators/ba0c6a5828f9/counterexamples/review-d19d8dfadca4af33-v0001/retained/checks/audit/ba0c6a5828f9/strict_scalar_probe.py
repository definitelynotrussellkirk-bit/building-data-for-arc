from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "ba0c6a5828f9"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators" / TASK_ID / "generator.py"
gen, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)

CASES = [
    {"seed": True, "sample_index": 0, "difficulty": "easy"},
    {"seed": 1.5, "sample_index": 0, "difficulty": "easy"},
    {"seed": "1", "sample_index": 0, "difficulty": "easy"},
    {"seed": 1, "sample_index": True, "difficulty": "easy"},
    {"seed": 1, "sample_index": 1.5, "difficulty": "easy"},
    {"seed": 1, "sample_index": "1", "difficulty": "easy"},
    {"seed": 1, "sample_index": -1, "difficulty": "easy"},
]


def value_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


rows = []
for case in CASES:
    row = {"arguments": case}
    try:
        profile = gen.schedule_profile(**case)
        row["schedule_profile"] = {"accepted": True, "profile": profile}
    except Exception as exc:
        row["schedule_profile"] = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        grid = gen.generate(**case)
        row["generate"] = {
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "observed": gen.observe_overrides(grid),
            "grid_sha256": value_hash(grid),
            "self_check": gen.self_check(grid),
        }
    except Exception as exc:
        row["generate"] = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}
    rows.append(row)

report = {
    "schema": "audit-strict-scalar-probe-v1",
    "task_id": TASK_ID,
    "finding_id": "A-BA0C-STRICT-SCALARS-1",
    "source_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "expected_contract": "seed and sample_index are exact non-negative integers; bool/float/string coercion is rejected",
    "cases": rows,
    "accepted_case_count": sum(1 for row in rows if row["generate"]["accepted"]),
}
out = Path(__file__).with_name("strict_scalar_probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
