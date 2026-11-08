#!/usr/bin/env python3
"""Finite adversarial shortcut scan for the two audit targets."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
OUT = ROOT / "checks/audits/shortcut_probe.json"


def load(task: str):
    path = REPO / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def bbox(cells):
    return [min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells)]


def endpoint_bbox(cells):
    first, last = cells[0], cells[-1]
    return [min(first[0], last[0]), min(first[1], last[1]),
            max(first[0], last[0]), max(first[1], last[1])]


def components(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    sizes = []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cell = (r + dr, c + dc)
                if cell in remaining:
                    remaining.remove(cell)
                    stack.append(cell)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def main() -> int:
    m3 = load("3a4b67ab16ff")
    scan3 = {"grids": 0, "colored_groups": 0, "endpoint_bbox_matches": 0, "violations": []}
    for band in (None, "easy", "medium", "hard"):
        for profile_index, profile in enumerate(m3.SCENE_PROFILES):
            for seed in range(100):
                grid = m3.generate(seed + 100_000 * profile_index, seed * 17,
                                   difficulty=band, scene_profile=profile)
                scan3["grids"] += 1
                for color in sorted(set(v for row in grid for v in row) - {0, 5}):
                    cells = [(r, c) for r, row in enumerate(grid)
                             for c, value in enumerate(row) if value == color]
                    scan3["colored_groups"] += 1
                    ok = bbox(cells) == endpoint_bbox(cells)
                    scan3["endpoint_bbox_matches"] += int(ok)
                    if not ok and len(scan3["violations"]) < 5:
                        scan3["violations"].append({"band": band, "profile": profile,
                                                    "seed": seed, "color": color, "cells": cells})

    grid3 = [[0] * 9 for _ in range(9)]
    for r in range(2, 7):
        for c in range(2, 7):
            grid3[r][c] = 5
    for r, c in ((2, 4), (4, 2), (4, 6), (6, 4)):
        grid3[r][c] = 3
    cells3 = [(r, c) for r, row in enumerate(grid3) for c, value in enumerate(row) if value == 3]
    correct3 = m3.rule_mirror(grid3)
    shortcut3 = [[0] * 9 for _ in range(9)]
    for r in range(2, 7):
        for c in range(2, 7):
            shortcut3[r][c] = 5
    ebox = endpoint_bbox(cells3)
    for r in range(max(ebox[0], 2), min(ebox[2], 6) + 1):
        for c in range(max(ebox[1], 2), min(ebox[3], 6) + 1):
            shortcut3[r][c] = 3

    m45 = load("45f08b9a5f47")
    scan45 = {"grids": 0, "color_groups": 0, "one_component_groups": 0,
              "largest_component_shortcut_matches": 0, "violations": []}
    for band in (None, "easy", "medium", "hard"):
        for seed in range(1000):
            grid = m45.generate(seed, seed * 19, difficulty=band)
            scan45["grids"] += 1
            colors = sorted(set(v for row in grid for v in row) - {0})
            counts = {color: sum(v == color for row in grid for v in row) for color in colors}
            comps = {color: components(grid, color) for color in colors}
            scan45["color_groups"] += len(colors)
            scan45["one_component_groups"] += sum(len(parts) == 1 for parts in comps.values())
            freq = min(counts, key=lambda color: (-counts[color], color))
            largest = min(comps, key=lambda color: (-comps[color][0], color))
            ok = freq == largest
            scan45["largest_component_shortcut_matches"] += int(ok)
            if not ok and len(scan45["violations"]) < 5:
                scan45["violations"].append({"band": band, "seed": seed,
                                              "counts": counts, "components": comps})

    grid45 = [[0] * 10 for _ in range(8)]
    for c in range(1, 5):
        grid45[1][c] = 2
    for c in range(6, 10):
        grid45[6][c] = 2
    for r in (3, 4):
        for c in (3, 4, 5):
            grid45[r][c] = 7
    for c in (1, 2):
        grid45[6][c] = 4
    counts45 = {color: sum(v == color for row in grid45 for v in row) for color in (2, 4, 7)}
    comps45 = {color: components(grid45, color) for color in counts45}
    winner45 = min(counts45, key=lambda color: (-counts45[color], color))
    shortcut_winner45 = min(comps45, key=lambda color: (-comps45[color][0], color))
    correct45 = [[value if value == winner45 else 0 for value in row] for row in grid45]
    shortcut45 = [[value if value == shortcut_winner45 else 0 for value in row] for row in grid45]

    report = {
        "3a4b67ab16ff": {
            "claim": "row-major first/last occurrence per color is sufficient on every sampled generated scene",
            "scan": scan3,
            "counterexample": {
                "input": grid3, "self_check": m3.self_check(grid3), "color_cells": cells3,
                "true_bbox": bbox(cells3), "row_major_endpoint_bbox": ebox,
                "canonical_output_python_mirror": correct3,
                "endpoint_shortcut_output": shortcut3, "different": correct3 != shortcut3,
            },
        },
        "45f08b9a5f47": {
            "claim": "keep the single largest connected component is sufficient on every sampled generated scene",
            "scan": scan45,
            "counterexample": {
                "input": grid45, "self_check": m45.self_check(grid45), "counts": counts45,
                "component_sizes": comps45, "canonical_winner_by_total_frequency": winner45,
                "largest_component_shortcut_winner": shortcut_winner45,
                "canonical_output_python_mirror": correct45,
                "largest_component_shortcut_output": shortcut45,
                "different": correct45 != shortcut45,
            },
        },
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({task: data["scan"] for task, data in report.items()}, indent=2))
    return 0 if all(data["counterexample"]["different"] for data in report.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
