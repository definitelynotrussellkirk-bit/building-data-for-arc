from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = REPO / "generators/664a918eb273/generator.py"
RUNTIME = REPO / "shared/runtime"
EXPECTED_SHA = "b6b2f5c0872fe92583cf63168b0bda683a8746ccd0181d71b18e142c4daf02b9"

sys.path.insert(0, str(RUNTIME))
spec = importlib.util.spec_from_file_location("ticket_api_boundary_664a918eb273", GENERATOR)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source_sha = hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
assert source_sha == EXPECTED_SHA
assert module.RULE_HASH == "0bf6f91bb8f8"
assert module.AXES["grid_w"]["valid"] == "8..30"

seed = int("dab4be008e8db3d0d7780026cbef253a7722e08629608f86271b8c31a5ae6093"[:16], 16)
valid_grid = module.generate(seed, 0, grid_w=8)
valid_observed = module.observe_overrides(valid_grid)
valid_self_check = module.self_check(valid_grid)

invalid = {"raised": False, "exception_type": None, "message": None}
try:
    module.generate(seed, 0, grid_w=7)
except Exception as exc:  # retain actual public behavior, including exact class/message
    invalid = {
        "raised": True,
        "exception_type": type(exc).__name__,
        "message": str(exc),
    }

result = {
    "schema": "arcpuzzles-api-boundary-probe-v1",
    "ticket_id": "ticket-a20a94207d73c098",
    "task_id": "664a918eb273",
    "source_sha256": source_sha,
    "rule_hash": module.RULE_HASH,
    "axis": "grid_w",
    "advertised_valid_domain": module.AXES["grid_w"]["valid"],
    "valid_call": {
        "kwargs": {"grid_w": 8},
        "returned_shape": [len(valid_grid), len(valid_grid[0])],
        "observed_overrides": valid_observed,
        "self_check_errors": valid_self_check,
    },
    "invalid_call": {
        "kwargs": {"grid_w": 7},
        **invalid,
    },
    "assessment": {
        "status": "boundary_honored",
        "finding": False,
        "summary": (
            "The documented lower endpoint grid_w=8 is realized exactly and passes self_check; "
            "the adjacent out-of-domain value grid_w=7 fails before generation with a clear ValueError."
        ),
    },
}

assert valid_observed["grid_w"] == 8
assert valid_self_check == []
assert invalid == {
    "raised": True,
    "exception_type": "ValueError",
    "message": "grid_w must lie in 8..30",
}

out = Path(__file__).with_name("result.json")
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "ticket_id": result["ticket_id"],
    "axis": result["axis"],
    "valid_width": valid_observed["grid_w"],
    "invalid_exception": invalid["exception_type"],
    "finding": result["assessment"]["finding"],
}, sort_keys=True))
