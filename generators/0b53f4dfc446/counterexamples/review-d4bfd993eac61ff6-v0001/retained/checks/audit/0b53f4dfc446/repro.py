#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK = "0b53f4dfc446"
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

rejected = None
try:
    module.generate(0, 0, difficulty="easy", grid_h=13)
except Exception as exc:
    rejected = {"type": type(exc).__name__, "message": str(exc)}

unknown_key = "__override_contract_unknown_axis__"
grid = module.generate(0, 0, difficulty="easy", **{unknown_key: 13})

here = Path(__file__).resolve().parent
(here / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(here / "repro.json").write_text(json.dumps({
    "task_id": TASK,
    "finding": "declared grid_h domain is not composable with difficulty; unknown keys are silently accepted",
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "rule_hash": rule_hash,
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "declared_override": {"grid_h": 13},
    "declared_override_result": rejected,
    "unknown_override": {unknown_key: 13},
    "unknown_override_accepted": True,
    "observed": {"grid_h": len(grid), "grid_w": len(grid[0])},
    "self_check": module.self_check(grid, difficulty="easy"),
    "input_path": "checks/audit/0b53f4dfc446/input.json",
    "racket_output_path": "checks/audit/0b53f4dfc446/racket.json",
    "repro_command": "PYTHONPATH=shared/runtime python3 ../checks/audit/0b53f4dfc446/repro.py",
    "official_gate": "checks/audit/0b53f4dfc446/override/result.json"
}, indent=2, sort_keys=True) + "\n")
print(json.dumps({"declared_override_result": rejected, "unknown_override_accepted": True}))
