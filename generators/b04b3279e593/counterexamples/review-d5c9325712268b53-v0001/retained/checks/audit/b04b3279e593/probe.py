#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3] / "repo"
TASK = "b04b3279e593"
SOURCE = REPO / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

seed, sample_index = 23, 7
base_overrides = {
    "grid_h": 5,
    "grid_w": 9,
    "markers": 3,
    "palette_kind": "warm",
    "anchor_corner": False,
    "asymmetry_force": False,
}
alternate_overrides = {
    **base_overrides,
    "palette_kind": "cool",
    "anchor_corner": True,
    "asymmetry_force": True,
}
base = mod.generate(seed, sample_index, difficulty="easy", **base_overrides)
alternate = mod.generate(seed, sample_index, difficulty="easy", **alternate_overrides)
degenerate = mod.generate(seed, sample_index, texture="no_markers")

(HERE / "input.json").write_text(json.dumps(base, indent=2) + "\n")
(HERE / "alternate_overrides_input.json").write_text(json.dumps(alternate, indent=2) + "\n")
(HERE / "invalid_degenerate_input.json").write_text(json.dumps(degenerate, indent=2) + "\n")
result = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": "easy",
    "base_overrides": base_overrides,
    "alternate_overrides": alternate_overrides,
    "advertised_controls_collide": base == alternate,
    "base_self_check": mod.self_check(base),
    "alternate_self_check": mod.self_check(alternate),
    "degenerate_texture": "no_markers",
    "degenerate_self_check": mod.self_check(degenerate),
    "paths": {
        "input": str((HERE / "input.json").relative_to(ROOT := HERE.parents[2])),
        "alternate": str((HERE / "alternate_overrides_input.json").relative_to(ROOT)),
        "degenerate": str((HERE / "invalid_degenerate_input.json").relative_to(ROOT)),
    },
}
assert result["advertised_controls_collide"] is True
assert result["base_self_check"] == []
assert result["alternate_self_check"] == []
assert result["degenerate_self_check"]
(HERE / "probe.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
