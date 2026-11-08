#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "b9d914a60205"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK_ID
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)


def attempt(label, *args, **kwargs):
    try:
        grid = GEN.generate(*args, **kwargs)
    except Exception as exc:
        return {"label": label, "status": "rejected", "error": f"{type(exc).__name__}: {exc}"}
    return {
        "label": label,
        "status": "accepted",
        "shape": [len(grid), len(grid[0])],
        "self_check": GEN.self_check(grid),
    }

report = {
    "task_id": TASK_ID,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "rule_hash_present": hasattr(GEN, "RULE_HASH"),
    "declared_grid_h": GEN.AXES["grid_h"],
    "declared_grid_w": GEN.AXES["grid_w"],
    "probes": [
        attempt("easy control", 0, 0, difficulty="easy"),
        attempt("declared easy grid_h=7", 0, 0, difficulty="easy", grid_h=7),
        attempt("declared easy grid_w=7", 0, 0, difficulty="easy", grid_w=7),
        attempt("unknown override", 0, 0, difficulty="easy", __override_contract_unknown_axis__=1),
        attempt("bool seed", True, 0, difficulty="easy"),
        attempt("negative sample_index", 0, -1, difficulty="easy"),
    ],
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, sort_keys=True))
