#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "repo" / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))


def load(task_id: str):
    path = ROOT / "repo" / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append({"color": color, "cells": sorted(cells)})
    return found


def main():
    key_gen = load("0e37f2aee589")
    key_grid = key_gen.generate(
        1,
        0,
        difficulty="easy",
        obj_size=12,
        n_distract=5,
    )
    key = key_grid[0][0]
    key_components = components(key_grid)
    distractor_components = [c for c in key_components if c["color"] != key]

    diamond_gen = load("d349f4dfe492")
    adjacent = [[0] * 5 for _ in range(5)]
    adjacent[2][2] = 3
    adjacent[2][3] = 6
    overlap = sorted(
        diamond_gen._diamond_zone(2, 2) & diamond_gen._diamond_zone(2, 3)
    )
    try:
        diamond_gen.generate(0, 0, difficulty="medium", n_seeds=5)
        seed_override = {"accepted": True}
    except Exception as exc:
        seed_override = {
            "accepted": False,
            "exception": f"{type(exc).__name__}: {exc}",
        }

    report = {
        "0e37f2aee589": {
            "request": {
                "seed": 1,
                "sample_index": 0,
                "difficulty": "easy",
                "obj_size": 12,
                "n_distract": 5,
            },
            "realized_distractor_components": len(distractor_components),
            "self_check": key_gen.self_check(key_grid),
            "grid": key_grid,
            "finding": "two failed distractor placements were silently ignored",
        },
        "d349f4dfe492": {
            "adjacent_seed_grid": adjacent,
            "diamond_zone_overlap_count": len(overlap),
            "self_check": diamond_gen.self_check(adjacent),
            "finding": "self_check accepts overlapping seed neighborhoods despite the invariant",
            "declared_valid_n_seeds_5": seed_override,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
