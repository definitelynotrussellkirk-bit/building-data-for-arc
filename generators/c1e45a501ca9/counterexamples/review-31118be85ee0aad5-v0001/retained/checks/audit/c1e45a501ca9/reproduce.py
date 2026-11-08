#!/usr/bin/env python3
"""Read-only exact-control audit for c1e45a501ca9."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
WORK = OUT.parents[2]
REPO = WORK / "repo"
SOURCE = REPO / "generators/c1e45a501ca9/generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))

spec = importlib.util.spec_from_file_location("audit_c1e45a501ca9", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

seed = 0
sample_index = 0
difficulty = "easy"
baseline = module.generate(seed, sample_index, difficulty=difficulty)
requested = {"n_cells": 1}
controlled = module.generate(seed, sample_index, difficulty=difficulty, **requested)
unknown = module.generate(seed, sample_index, difficulty=difficulty, typo_axis=123)

def source_cells(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 8)]

record = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "generator_version": module.VERSION,
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "overrides": requested,
    "declared_axis": module.AXES["n_cells"],
    "observed": {
        "shape": [len(controlled), len(controlled[0])],
        "n_cells": len(source_cells(controlled)),
        "source_cells": source_cells(controlled),
        "self_check": module.self_check(controlled, difficulty=difficulty),
        "same_as_baseline": controlled == baseline,
    },
    "unknown_override_probe": {
        "overrides": {"typo_axis": 123},
        "accepted": True,
        "same_as_baseline": unknown == baseline,
        "self_check": module.self_check(unknown, difficulty=difficulty),
    },
    "input": controlled,
    "domain_membership": "actual ordinary generate() output; validator-clean",
    "finding": "declared exact n_cells=1 is ignored (two cells emitted), and an unknown key is silently accepted",
    "supported_apply": {
        "cwd": "packet_root",
        "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", module.TASK_ID, "--input", "../checks/audit/c1e45a501ca9/input.json", "--out", "../checks/audit/c1e45a501ca9/racket.json"],
    },
}
(OUT / "input.json").write_text(json.dumps(controlled, indent=2) + "\n", encoding="utf-8")
(OUT / "counterexample.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": module.TASK_ID,
    "generator_sha256": record["generator_sha256"],
    "requested_n_cells": 1,
    "observed_n_cells": record["observed"]["n_cells"],
    "self_check": record["observed"]["self_check"],
    "unknown_override_accepted": True,
    "same_as_baseline": record["observed"]["same_as_baseline"],
}, indent=2))
if record["observed"]["n_cells"] == 1 or record["observed"]["self_check"]:
    raise SystemExit(1)
