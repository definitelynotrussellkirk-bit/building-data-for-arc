from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "3031e2ee53d1"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)

cases = [
    {"seed": True, "sample_index": 0},
    {"seed": 1.0, "sample_index": 0},
    {"seed": "1", "sample_index": 0},
    {"seed": 1, "sample_index": True},
    {"seed": 1, "sample_index": 1.0},
    {"seed": 1, "sample_index": "1"},
    {"seed": 1, "sample_index": -1},
]
receipts = []
for case in cases:
    try:
        grid = GEN.generate(case["seed"], case["sample_index"])
    except Exception as exc:
        receipts.append({**case, "accepted": False, "error": f"{type(exc).__name__}: {exc}"})
    else:
        receipts.append({
            **case,
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "self_check": GEN.self_check(grid),
            "grid_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
        })

if not all(row["accepted"] for row in receipts):
    raise SystemExit("expected current scalar-coercion defect did not reproduce")
if any(row["self_check"] for row in receipts):
    raise SystemExit("accepted scalar aliases did not produce lawful grids")

# Exact alias evidence: schedule_profile itself coerces sample_index with int().
aliases = {
    "int_1": GEN.schedule_profile(7, 1),
    "bool_true": GEN.schedule_profile(7, True),
    "float_1": GEN.schedule_profile(7, 1.0),
    "string_1": GEN.schedule_profile(7, "1"),
}
if len(set(aliases.values())) != 1:
    raise SystemExit("schedule scalar aliases no longer collapse")

report = {
    "schema": "audit-3031e2ee53d1-strict-scalars-v1",
    "status": "reproduced",
    "task_id": TASK,
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "rule_hash": GEN.RULE_HASH,
    "finding": (
        "generate accepts bool, float, string aliases for seed/sample_index and a negative sample_index; "
        "schedule_profile explicitly coerces sample_index with int()."
    ),
    "accepted_invalid_calls": receipts,
    "schedule_aliases": aliases,
    "expected_contract": (
        "seed and sample_index should be literal Python integers, and sample_index should be nonnegative, "
        "so invalid caller data fails closed rather than changing or aliasing the curriculum schedule."
    ),
    "limits": [
        "This probe covers scalar call validation only; it does not challenge the Racket transformation.",
        "No audit-target source was modified.",
    ],
}
(HERE / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "reproduced", "source_sha256": SOURCE_SHA, "accepted_invalid_calls": len(receipts)}))
