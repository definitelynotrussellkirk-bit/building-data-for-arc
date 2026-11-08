#!/usr/bin/env python3
"""Reproduce the 966f31e63b08 override-contract audit finding."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "repo/generators/966f31e63b08/generator.py"
OUT = Path(__file__).with_name("override-counterexample.json")


def load_module():
    spec = importlib.util.spec_from_file_location("audit_966f31e63b08_generator", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    seed, sample_index, difficulty = 19, 7, "medium"
    overrides = {
        "grid_h": 15,
        "grid_w": 15,
        "template_kind": "cross",
        "n_footprints": 9,
        "five_density": 0.56,
        "palette_size": 3,
        "position_bias": "dense_field_with_carved_footprints",
    }
    base = module.generate(seed, sample_index, difficulty=difficulty)
    forced = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
    unknown = module.generate(
        seed, sample_index, difficulty=difficulty, __audit_unknown_axis__=123
    )
    result = {
        "schema": "audit-override-counterexample-v1",
        "task_id": "966f31e63b08",
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
        "base_grid": base,
        "forced_grid": forced,
        "unknown_key_grid": unknown,
        "base_equals_forced": base == forced,
        "base_equals_unknown": base == unknown,
        "base_shape": [len(base), len(base[0])],
        "requested_shape": [15, 15],
        "forced_self_check": module.self_check(forced, difficulty=difficulty),
        "finding": "advertised exact overrides and an unknown key are silently ignored",
    }
    assert result["base_equals_forced"]
    assert result["base_equals_unknown"]
    assert result["base_shape"] != result["requested_shape"]
    assert result["forced_self_check"] == []
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "task_id", "generator_sha256", "base_equals_forced",
        "base_equals_unknown", "base_shape", "requested_shape", "finding"
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
