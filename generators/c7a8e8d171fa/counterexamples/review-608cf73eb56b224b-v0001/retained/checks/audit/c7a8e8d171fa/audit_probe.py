"""Read-only audit probe for c7a8e8d171fa's advertised generator contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
WORK = next(parent for parent in HERE.parents if (parent / "repo").is_dir())
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "c7a8e8d171fa"
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=REPO)


def grid_sha(grid):
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def call(kwargs):
    try:
        grid = gen.generate(0, 0, **kwargs)
    except Exception as exc:  # evidence captures the public failure verbatim
        return {
            "kwargs": kwargs,
            "status": "raised",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }
    return {
        "kwargs": kwargs,
        "status": "returned",
        "shape": [len(grid), len(grid[0]) if grid else 0],
        "grid_sha256": grid_sha(grid),
        "self_check": gen.self_check(grid),
        "grid": grid,
    }

pairs = {
    "palette_kind": [call({"palette_kind": "warm"}), call({"palette_kind": "cool"})],
    "anchor_corner": [call({"anchor_corner": False}), call({"anchor_corner": True})],
    "asymmetry_force": [call({"asymmetry_force": False}), call({"asymmetry_force": True})],
    "texture": [call({"texture": "warm"}), call({"texture": "cool"})],
}

result = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "source_path": str(source_path.relative_to(WORK)),
    "source_sha256": source_sha256,
    "version": getattr(gen, "VERSION", None),
    "rule_hash_pin": getattr(gen, "RULE_HASH", None),
    "advertised_axes": gen.AXES,
    "seed": 0,
    "sample_index": 0,
    "ignored_axis_pairs": pairs,
    "pair_outputs_identical": {
        name: rows[0].get("grid_sha256") == rows[1].get("grid_sha256")
        for name, rows in pairs.items()
    },
    "advertised_grid_boundaries": [
        call({"grid_h": 5, "grid_w": 5}),
        call({"grid_h": 24, "grid_w": 24}),
    ],
    "unknown_axis": call({"unknown_axis": 123}),
}

output = HERE.with_name("audit_probe.json")
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "output": str(output.relative_to(WORK)),
    "source_sha256": source_sha256,
    "pair_outputs_identical": result["pair_outputs_identical"],
    "boundary_statuses": [row["status"] for row in result["advertised_grid_boundaries"]],
    "unknown_axis_status": result["unknown_axis"]["status"],
}, indent=2, sort_keys=True))
