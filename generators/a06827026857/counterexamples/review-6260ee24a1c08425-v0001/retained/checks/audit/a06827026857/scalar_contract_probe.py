from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "a06827026857"
ROOT = Path.cwd().resolve()
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)
OUT = ROOT.parent / "checks" / "audit" / TASK

cases = [
    ("seed_bool", {"seed": True, "sample_index": 0, "difficulty": "medium"}),
    ("seed_float", {"seed": 1.0, "sample_index": 0, "difficulty": "medium"}),
    ("seed_string", {"seed": "1", "sample_index": 0, "difficulty": "medium"}),
    ("sample_index_bool", {"seed": 1, "sample_index": True, "difficulty": "medium"}),
    ("sample_index_false", {"seed": 1, "sample_index": False, "difficulty": "medium"}),
    ("sample_index_negative", {"seed": 1, "sample_index": -1, "difficulty": "medium"}),
    ("difficulty_unknown", {"seed": 1, "sample_index": 0, "difficulty": "weird"}),
    ("difficulty_integer", {"seed": 1, "sample_index": 0, "difficulty": 1}),
]
results = []
for name, kwargs in cases:
    item = {"case": name, "arguments": kwargs}
    try:
        grid = GEN.generate(**kwargs)
    except Exception as exc:
        item.update(
            accepted=False,
            exception=type(exc).__name__,
            message=str(exc),
        )
    else:
        item.update(
            accepted=True,
            shape=[len(grid), len(grid[0])],
            self_check=GEN.self_check(grid),
            observed=GEN.observe_overrides(grid),
            grid_sha256=hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest(),
        )
    results.append(item)

# Controls demonstrate that the module already treats coercible override values
# strictly, so acceptance is specific to the top-level call contract.
control_results = []
for axis, value in (("grid_h", True), ("grid_h", 9.0), ("grid_h", "9")):
    try:
        GEN.generate(1, 0, difficulty="medium", **{axis: value})
    except Exception as exc:
        control_results.append(
            {"axis": axis, "value": repr(value), "rejected": True,
             "exception": type(exc).__name__, "message": str(exc)}
        )
    else:
        control_results.append(
            {"axis": axis, "value": repr(value), "rejected": False}
        )

accepted = [item["case"] for item in results if item["accepted"]]
report = {
    "schema": "arcpuzzles-audit-scalar-contract-v1",
    "task_id": TASK,
    "generator_sha256": SOURCE_SHA,
    "generator_version": GEN.VERSION,
    "accepted_invalid_calls": accepted,
    "cases": results,
    "strict_override_controls": control_results,
    "reproduced": (
        accepted == [name for name, _ in cases]
        and all(not item["self_check"] for item in results if item["accepted"])
        and all(item["rejected"] for item in control_results)
    ),
    "classification": (
        "call-contract validation gap: bool/coercible seeds, bool/negative "
        "sample indices, and unknown/non-string difficulty values are silently accepted"
    ),
    "impact": (
        "invalid callers can enter undocumented schedule branches or fallback "
        "difficulty behavior while producing validator-clean grids; labels are not shown wrong"
    ),
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "scalar-contract-report.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["reproduced"] else 1)
