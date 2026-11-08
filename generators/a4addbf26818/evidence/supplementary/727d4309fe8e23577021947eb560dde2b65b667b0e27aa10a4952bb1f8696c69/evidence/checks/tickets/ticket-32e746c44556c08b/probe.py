from __future__ import annotations
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "a4addbf26818"
SEED_HEX = "ac082157edfee9a09daf9673e739f4df749b50a2e4d8252342a9e471c7b13adf"
SEED = int(SEED_HEX[:16], 16)
SAMPLE_INDEX = 0
DIFFICULTY = "easy"
ROOT = Path.cwd()
module, source_path, source_hash = load_selected_generator(TASK_ID, root=ROOT)


def call(overrides):
    try:
        grid = module.generate(
            SEED,
            SAMPLE_INDEX,
            difficulty=DIFFICULTY,
            **overrides,
        )
    except Exception as exc:
        return {
            "accepted": False,
            "exception": f"{type(exc).__name__}: {exc}",
        }
    return {
        "accepted": True,
        "exception": None,
        "observed_grid_h": len(grid),
        "observed_grid_w": len(grid[0]),
        "self_check_errors": module.self_check(grid, difficulty=DIFFICULTY),
        "grid_sha256": hashlib.sha256(
            json.dumps(grid, separators=(",", ":")).encode()
        ).hexdigest(),
        "grid": grid,
    }

valid = call({"grid_h": 6})
invalid = call({"grid_h": 5})
report = {
    "schema": "supplementary-api-boundary-v1",
    "ticket_id": "ticket-32e746c44556c08b",
    "task_id": TASK_ID,
    "generator_sha256": source_hash,
    "generator_version": module.VERSION,
    "declared_rule_hash": getattr(module, "RULE_HASH", None),
    "seed_hex": SEED_HEX,
    "seed_int": SEED,
    "sample_index": SAMPLE_INDEX,
    "difficulty": DIFFICULTY,
    "axis": "grid_h",
    "advertised": module.AXES["grid_h"],
    "valid_request": {"grid_h": 6},
    "invalid_request": {"grid_h": 5},
    "valid_result": valid,
    "invalid_result": invalid,
    "valid_boundary_realized_exactly": valid.get("observed_grid_h") == 6,
    "invalid_boundary_rejected": invalid["accepted"] is False,
    "same_output": (
        valid.get("grid_sha256") == invalid.get("grid_sha256")
        if valid["accepted"] and invalid["accepted"]
        else None
    ),
}
report["status"] = (
    "completed"
    if report["valid_boundary_realized_exactly"] and report["invalid_boundary_rejected"]
    else "finding"
)
out = ROOT.parent / "checks/tickets/ticket-32e746c44556c08b/boundary.json"
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "status": report["status"],
    "valid_accepted": valid["accepted"],
    "valid_observed_grid_h": valid.get("observed_grid_h"),
    "invalid_accepted": invalid["accepted"],
    "invalid_observed_grid_h": invalid.get("observed_grid_h"),
    "same_output": report["same_output"],
}, sort_keys=True))
