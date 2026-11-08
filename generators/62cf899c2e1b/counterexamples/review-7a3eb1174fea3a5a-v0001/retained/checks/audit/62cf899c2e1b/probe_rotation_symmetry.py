#!/usr/bin/env python3
"""Find a normal generated input with only two distinct rotations."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HOME = Path(__file__).resolve().parents[3] / "repo" / "generators" / "62cf899c2e1b"
SOURCE = HOME / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_62cf899c2e1b", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rot_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def collage(grid):
    r90 = rot_cw(grid)
    r180 = rot_cw(r90)
    r270 = rot_cw(r180)
    return [
        left + right
        for left, right in zip(grid + r180, r270 + r90)
    ]


def main():
    gen = load_generator()
    witness = None
    checked = 0
    for seed in range(2000):
        grid = gen.generate(
            seed,
            seed * 17 + 5,
            difficulty="easy",
            grid_n=3,
            palette_size=2,
            texture="stripes",
            bg_density=0.0,
            noise_overlay=0.0,
            asymmetry_force=True,
        )
        checked += 1
        rotations = [grid]
        for _ in range(3):
            rotations.append(rot_cw(rotations[-1]))
        encoded = {json.dumps(item, separators=(",", ":")) for item in rotations}
        if len(encoded) < 4 and gen.self_check(grid) == []:
            witness = {
                "seed": seed,
                "sample_index": seed * 17 + 5,
                "overrides": {
                    "difficulty": "easy",
                    "grid_n": 3,
                    "palette_size": 2,
                    "texture": "stripes",
                    "bg_density": 0.0,
                    "noise_overlay": 0.0,
                    "asymmetry_force": True,
                },
                "input": grid,
                "rotations_cw_0_90_180_270": rotations,
                "distinct_rotation_count": len(encoded),
                "private_4fold_check": gen._is_4fold_sym(grid, len(grid)),
                "self_check": gen.self_check(grid),
                "output_collage": collage(grid),
            }
            break
    report = {
        "task_id": gen.TASK_ID,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "checked": checked,
        "finding": "normal asymmetry_force=True generation can have fewer than four distinct rotations",
        "witness": witness,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if witness is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
