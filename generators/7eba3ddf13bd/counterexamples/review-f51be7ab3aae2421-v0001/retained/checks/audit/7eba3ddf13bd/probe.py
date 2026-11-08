#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "7eba3ddf13bd"
EXPECTED_SHA = "5ce1865b3bce007f9510fee7a6a12c33857940280f827cd347627ae99a9d5c6b"
module, source, digest = load_selected_generator(TASK_ID, root=REPO)
if digest != EXPECTED_SHA:
    raise RuntimeError(f"source hash drift: expected {EXPECTED_SHA}, got {digest}")


def grid_digest(grid):
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return {
        "grid_sha256": hashlib.sha256(raw).hexdigest(),
        "shape": [len(grid), len(grid[0])],
        "self_check": module.self_check(grid),
    }


def call(seed, sample_index, difficulty):
    try:
        grid = module.generate(seed, sample_index, difficulty=difficulty)
    except Exception as exc:  # evidence records exact rejection/acceptance
        return {"status": "rejected", "exception": type(exc).__name__, "message": str(exc)}
    return {"status": "accepted", **grid_digest(grid)}

probes = []
for difficulty in ("easy", None, "hard"):
    for value in (True, False, 1.0, 1.75, "1"):
        probes.append({
            "axis": "seed",
            "value_repr": repr(value),
            "value_type": type(value).__name__,
            "difficulty": difficulty,
            "result": call(value, 0, difficulty),
        })
    for value in (True, False, -1):
        probes.append({
            "axis": "sample_index",
            "value_repr": repr(value),
            "value_type": type(value).__name__,
            "difficulty": difficulty,
            "result": call(991, value, difficulty),
        })

report = {
    "schema": "review-audit-strict-call-probe-v1",
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(REPO)),
    "generator_sha256": digest,
    "legal_control": {"seed": 991, "sample_index": 0, "difficulty": None,
                      "result": call(991, 0, None)},
    "probes": probes,
    "accepted_invalid_count": sum(row["result"]["status"] == "accepted" for row in probes),
    "probe_count": len(probes),
    "note": "These are call-boundary contract probes; no semantic rival or Racket output is implicated.",
}
(HERE / "probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": digest,
    "accepted_invalid_count": report["accepted_invalid_count"],
    "probe_count": report["probe_count"],
    "legal_control": report["legal_control"],
}, indent=2))
