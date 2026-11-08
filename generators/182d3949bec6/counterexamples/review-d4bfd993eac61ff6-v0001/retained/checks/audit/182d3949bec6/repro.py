#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK = "182d3949bec6"
GENERATOR = ROOT / "generators" / TASK / "generator.py"
CANONICAL = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
sys.path.insert(0, str(ROOT / "shared" / "runtime"))

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GENERATOR)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

rule_source = None
for line in CANONICAL.read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") == TASK:
        rule_source = row["program_solution"]
        break
assert rule_source is not None
rule_hash = hashlib.sha256(" ".join(rule_source.split()).encode()).hexdigest()[:12]

requested = {"grid_h": 12, "grid_w": 16}
grid = module.generate(0, 0, difficulty="easy", **requested)
observed = {"grid_h": len(grid), "grid_w": len(grid[0])}

here = Path(__file__).resolve().parent
(here / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(here / "repro.json").write_text(json.dumps({
    "task_id": TASK,
    "finding": "declared exact grid_h/grid_w overrides are ignored",
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "rule_hash": rule_hash,
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "overrides": requested,
    "observed": observed,
    "mismatch": observed != requested,
    "self_check": module.self_check(grid, difficulty="easy"),
    "input_path": "checks/audit/182d3949bec6/input.json",
    "racket_output_path": "checks/audit/182d3949bec6/racket.json",
    "repro_command": "PYTHONPATH=shared/runtime python3 ../checks/audit/182d3949bec6/repro.py",
    "official_gate": "checks/audit/182d3949bec6/override/result.json"
}, indent=2, sort_keys=True) + "\n")
print(json.dumps({"requested": requested, "observed": observed, "mismatch": observed != requested}))
