#!/usr/bin/env python3
"""Reproduce dead and non-strict overrides in generator 1b6b40a92e4f."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "1b6b40a92e4f"
REPO = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def digest(grid):
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def main():
    gen = load_generator()
    seed, sample_index, difficulty = 17, 3, "medium"
    calls = {
        "control": {},
        "grid_min": {"grid_h": 9, "grid_w": 10},
        "grid_max": {"grid_h": 16, "grid_w": 18},
        "palette_warm": {"palette_kind": "warm"},
        "palette_cool": {"palette_kind": "cool"},
        "anchor_true": {"anchor_corner": True},
        "anchor_false": {"anchor_corner": False},
        "asymmetry_true": {"asymmetry_force": True},
        "asymmetry_false": {"asymmetry_force": False},
        "unknown_key": {"unknown_axis": "accepted"},
    }
    observations = {}
    for name, overrides in calls.items():
        grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
        observations[name] = {
            "overrides": overrides,
            "shape": [len(grid), len(grid[0])],
            "sha256": digest(grid),
            "self_check": gen.self_check(grid),
        }
    unique_hashes = sorted({row["sha256"] for row in observations.values()})
    retained_racket = json.loads((Path(__file__).with_name("racket.json")).read_text())
    result = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "rule_hash": retained_racket["executed_rule_hash"],
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "observations": observations,
        "unique_grid_hashes": unique_hashes,
        "all_calls_byte_identical": len(unique_hashes) == 1,
        "requested_grid_min": [9, 10],
        "observed_grid_min": observations["grid_min"]["shape"],
        "unknown_override_rejected": False,
        "racket_evidence": "checks/audit/1b6b40a92e4f/racket.json",
        "interpretation": (
            "The advertised grid_h, grid_w, palette_kind, anchor_corner, and "
            "asymmetry_force controls are dead for this exact call, and an unknown key is silently accepted."
        ),
    }
    assert result["all_calls_byte_identical"]
    assert result["observed_grid_min"] != result["requested_grid_min"]
    Path(__file__).with_name("probe.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "all_calls_byte_identical": result["all_calls_byte_identical"],
        "requested_grid_min": result["requested_grid_min"],
        "observed_grid_min": result["observed_grid_min"],
        "unique_grid_hashes": unique_hashes,
    }, indent=2))


if __name__ == "__main__":
    main()
