#!/usr/bin/env python3
"""Reproduce the two assigned adversarial audit findings.

This is evidence-only: it imports the frozen assigned generators, compares each
canonical Python oracle with a plausible shortcut across deterministic samples,
and then prints one lawful counterexample absent from the generated support.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

Grid = list[list[int]]


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def foreign_diagonal_shortcut(grid: Grid) -> Grid:
    """Wrong 746 shortcut: diagonals must not contain a foreign color."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            arms = [grid[r - 1][c], grid[r + 1][c], grid[r][c - 1], grid[r][c + 1]]
            if arms[0] == 0 or len(set(arms)) != 1:
                continue
            color = arms[0]
            neighborhood = [
                grid[rr][cc]
                for rr in range(r - 1, r + 2)
                for cc in range(c - 1, c + 2)
                if grid[rr][cc] != 0
            ]
            if all(value == color for value in neighborhood):
                out[r][c] = color
    return out


def yellow_anchor_shortcut(grid: Grid) -> Grid:
    """Wrong d306 shortcut: existing yellow resets diagonal alternation."""
    out = [row[:] for row in grid]
    groups: dict[int, list[tuple[int, int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                groups.setdefault(r - c, []).append((r, c, value))
    for cells in groups.values():
        cells.sort()
        yellow = next((i for i, (_, _, value) in enumerate(cells) if value == 4), None)
        if yellow is None:
            recolor = range(1, len(cells), 2)
        else:
            # Leave all cells before the first yellow unchanged and restart there.
            recolor = range(yellow + 1, len(cells), 2)
        for i in recolor:
            r, c, _ = cells[i]
            out[r][c] = 4
    return out


def compare_generated(task_id: str, rival: Callable[[Grid], Grid], per_band: int) -> dict:
    module = load(task_id)
    mismatches = []
    bands = (None, "easy", "medium", "hard")
    for band_index, band in enumerate(bands):
        for i in range(per_band):
            seed = 730_000_000 + band_index * 1_000_000 + i
            sample_index = i
            grid = module.generate(seed, sample_index, difficulty=band)
            expected = module.rule_mirror(grid)
            actual = rival(grid)
            if actual != expected:
                mismatches.append({"band": band, "seed": seed, "sample_index": sample_index})
                if len(mismatches) >= 5:
                    return {"draws": (band_index * per_band + i + 1), "mismatches": mismatches}
    return {"draws": len(bands) * per_band, "mismatches": mismatches}


def rows(grid: Grid) -> list[str]:
    return ["".join(str(value) for value in row) for row in grid]


def main() -> None:
    g746 = load("746afba14f72")
    scan746 = compare_generated("746afba14f72", foreign_diagonal_shortcut, 500)
    ce746 = [[0] * 5 for _ in range(5)]
    ce746[1][1] = 7
    ce746[1][2] = 2
    ce746[2][1] = 2
    ce746[2][3] = 2
    ce746[3][2] = 2
    result746 = {
        "generated_scan": scan746,
        "counterexample_input": rows(ce746),
        "self_check": g746.self_check(ce746),
        "canonical_output": rows(g746.rule_mirror(ce746)),
        "shortcut_output": rows(foreign_diagonal_shortcut(ce746)),
        "center": {
            "canonical": g746.rule_mirror(ce746)[2][2],
            "shortcut": foreign_diagonal_shortcut(ce746)[2][2],
        },
    }

    gd306 = load("d306f84259e3")
    scand306 = compare_generated("d306f84259e3", yellow_anchor_shortcut, 1000)
    ced306 = [[0] * 5 for _ in range(5)]
    for i, value in enumerate((2, 2, 4, 2)):
        ced306[i][i] = value
    resultd306 = {
        "generated_scan": scand306,
        "counterexample_input": rows(ced306),
        "self_check": gd306.self_check(ced306),
        "scene_profile": gd306._analysis(ced306)["scene_profile"],
        "canonical_output": rows(gd306.rule_mirror(ced306)),
        "shortcut_output": rows(yellow_anchor_shortcut(ced306)),
        "main_diagonal": {
            "canonical": [gd306.rule_mirror(ced306)[i][i] for i in range(4)],
            "shortcut": [yellow_anchor_shortcut(ced306)[i][i] for i in range(4)],
        },
    }

    payload = {"746afba14f72": result746, "d306f84259e3": resultd306}
    print(json.dumps(payload, indent=2, sort_keys=True))
    assert scan746["mismatches"] == []
    assert result746["self_check"], "expected current checker to reject foreign diagonal"
    assert result746["center"] == {"canonical": 2, "shortcut": 0}
    assert scand306["mismatches"] == []
    assert resultd306["self_check"] == []
    assert resultd306["scene_profile"] == "existing_yellow"
    assert resultd306["main_diagonal"] == {
        "canonical": [2, 4, 4, 4],
        "shortcut": [2, 2, 4, 4],
    }


if __name__ == "__main__":
    main()
