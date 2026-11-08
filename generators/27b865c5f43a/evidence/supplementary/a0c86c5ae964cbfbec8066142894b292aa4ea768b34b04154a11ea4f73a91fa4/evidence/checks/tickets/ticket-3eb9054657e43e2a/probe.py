#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from reviewer_support import find_root, load_selected_generator

TASK_ID = "27b865c5f43a"
EXPECTED_SHA = "495ba0e0517cf001c44dfcd69c0ca56e98e4bc767fdcfd76e56e726424be377e"
start = time.monotonic()
root = find_root(__file__)
generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
assert source_sha == EXPECTED_SHA
assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED_SHA

valid_grid = generator.generate(0, 0, grid_h=8)
valid_observed = generator.observe_overrides(valid_grid)
assert len(valid_grid) == 8
assert generator.self_check(valid_grid) == []
assert valid_observed["grid_h"] == 8

invalid = None
try:
    generator.generate(0, 0, grid_h=True)
except Exception as exc:  # exact behavior retained below
    invalid = {"type": type(exc).__name__, "message": str(exc)}
else:
    raise AssertionError("bool grid_h override was accepted")
assert invalid["type"] == "TypeError"
assert "grid_h must be an integer, not bool" in invalid["message"]

result = {
    "ticket_id": "ticket-3eb9054657e43e2a",
    "type": "api_boundary",
    "status": "completed",
    "source": {
        "path": str(source.relative_to(root)),
        "sha256": source_sha,
    },
    "boundary": "grid_h exact-int override: 8 accepted, bool True rejected",
    "valid_call": {
        "kwargs": {"grid_h": 8},
        "height": len(valid_grid),
        "width": len(valid_grid[0]),
        "observed_grid_h": valid_observed["grid_h"],
        "self_check_errors": [],
    },
    "invalid_call": {
        "kwargs": {"grid_h": True},
        "exception": invalid,
    },
    "finding": None,
    "elapsed_seconds": round(time.monotonic() - start, 6),
}
Path(__file__).with_name("result.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, sort_keys=True))
