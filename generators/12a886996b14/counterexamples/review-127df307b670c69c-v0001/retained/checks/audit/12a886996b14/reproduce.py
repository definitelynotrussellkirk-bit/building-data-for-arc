#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

TASK = "12a886996b14"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GENERATOR_PATH = ROOT / "generators" / TASK / "generator.py"
OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("audit_generator", GENERATOR_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

grid = module.generate(0, 0, texture="no_red")
(OUT / "no_red_input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
observation = {
    "generator_version": module.VERSION,
    "seed": 0,
    "sample_index": 0,
    "override": {"texture": "no_red"},
    "self_check": module.self_check(grid),
    "red_count": sum(value == 2 for row in grid for value in row),
    "green_count": sum(value == 3 for row in grid for value in row),
    "yellow_count": sum(value == 4 for row in grid for value in row),
}
(OUT / "no_red_observation.json").write_text(json.dumps(observation, indent=2) + "\n")
print(json.dumps(observation, indent=2))
