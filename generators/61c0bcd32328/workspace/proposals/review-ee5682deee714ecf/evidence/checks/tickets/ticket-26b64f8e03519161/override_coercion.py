"""Replay silent coercion of non-integer exact-axis overrides."""
from __future__ import annotations

from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GENERATOR = REPO / "generators" / "260f488cb5a8" / "generator.py"

spec = spec_from_file_location("audit_260f488cb5a8", GENERATOR)
assert spec and spec.loader
module = module_from_spec(spec)
spec.loader.exec_module(module)

cases = []
for requested in (
    {"grid_h": 4.9},
    {"grid_w": "8"},
    {"grid_w": 8.7},
):
    try:
        grid = module.generate(1, 2, difficulty="medium", **requested)
        cases.append(
            {
                "requested": requested,
                "status": "accepted",
                "observed": module.observe_overrides(grid),
                "self_check": module.self_check(grid),
            }
        )
    except Exception as exc:
        cases.append(
            {
                "requested": requested,
                "status": "rejected",
                "exception": f"{type(exc).__name__}: {exc}",
            }
        )

result = {
    "schema": "audit-reproduction-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": sha256(GENERATOR.read_bytes()).hexdigest(),
    "replay": {"seed": 1, "sample_index": 2, "difficulty": "medium"},
    "cases": cases,
    "finding": (
        "grid_h/grid_w are declared integer exact controls, but draw_int coerces "
        "floats and numeric strings; accepted pixels do not equal the requested values."
    ),
}
print(json.dumps(result, indent=2, sort_keys=True))
