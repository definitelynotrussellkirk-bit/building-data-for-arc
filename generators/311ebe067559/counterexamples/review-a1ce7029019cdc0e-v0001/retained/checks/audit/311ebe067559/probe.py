#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "311ebe067559"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def record(name, kwargs):
    grid = GEN.generate(20261020, 17, difficulty="medium", **kwargs)
    return {
        "name": name,
        "kwargs": kwargs,
        "shape": [len(grid), len(grid[0])],
        "sha256": digest(grid),
        "self_check": GEN.self_check(grid),
        "grid": grid,
    }


cases = [
    record("grid_h_low", {"grid_h": 7}),
    record("grid_h_high", {"grid_h": 14}),
    record("grid_w_low", {"grid_w": 9}),
    record("grid_w_high", {"grid_w": 16}),
]
report = {
    "schema": "arcpuzzles-audit-override-probe-v1",
    "task_id": TASK_ID,
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "generator_version": GEN.VERSION,
    "declared_rule_hash": GEN.RULE_HASH,
    "finding": "advertised exact grid_h/grid_w overrides are not consumed",
    "cases": cases,
    "assertions": {
        "grid_h_14_honored": cases[1]["shape"][0] == 14,
        "grid_w_16_honored": cases[3]["shape"][1] == 16,
        "paired_grid_h_calls_identical": cases[0]["sha256"] == cases[1]["sha256"],
        "paired_grid_w_calls_identical": cases[2]["sha256"] == cases[3]["sha256"],
    },
    "scope": "one seed/index at medium difficulty; no target files edited",
}
out = Path(__file__).with_name("probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report["assertions"], sort_keys=True))
