"""Independent review helpers for ARC task 891a82451a8a.

This module deliberately does not import implementation helpers from generator.py.
It is used by the retained task-local regression suite and by future reviewers.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import os
from pathlib import Path
from typing import Any

TASK_ID = "891a82451a8a"
CYCLE = (0, 5, 2, 8, 9, 6, 1, 3, 4)
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    candidate = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py")
    spec = importlib.util.spec_from_file_location("reviewed_891a82451a8a", candidate.resolve())
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def analyze(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("rows must be non-empty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")

    height = len(grid)
    counts = Counter(value for row in grid for value in row)
    ranked = counts.most_common()
    if len(ranked) < 2 or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
        raise ValueError("grid must have a unique modal background and a singleton seed")
    background = ranked[0][0]
    if background == 0:
        raise ValueError("background 0 is outside the selected Racket rule domain")
    seed_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    ]
    if len(seed_cells) != 1:
        raise ValueError(f"expected one non-background seed, found {len(seed_cells)}")
    seed_row, seed_col = seed_cells[0]
    seed_color = grid[seed_row][seed_col]
    if seed_color not in CYCLE:
        raise ValueError(f"seed color {seed_color} is not in the fixed cycle")
    return {
        "height": height,
        "width": width,
        "background": background,
        "seed_row": seed_row,
        "seed_col": seed_col,
        "seed_color": seed_color,
        "seed_region": classify_region(height, width, seed_row, seed_col),
    }


def classify_region(height: int, width: int, row: int, col: int) -> str:
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    if (row, col) in corners:
        return "corner"
    if row in (0, height - 1) or col in (0, width - 1):
        return "edge"
    center_rows = {(height - 1) // 2, height // 2}
    center_cols = {(width - 1) // 2, width // 2}
    if row in center_rows and col in center_cols:
        return "center"
    return "interior"


def observed(grid: list[list[int]]) -> dict[str, Any]:
    info = analyze(grid)
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "bg_color": info["background"],
        "seed_color": info["seed_color"],
        "seed_region": info["seed_region"],
    }


def expected_output(
    grid: list[list[int]],
    *,
    metric: str = "manhattan",
    fixed_phase: int | None = None,
    fixed_anchor: tuple[int, int] | None = None,
) -> list[list[int]]:
    info = analyze(grid)
    anchor = fixed_anchor or (info["seed_row"], info["seed_col"])
    start = CYCLE.index(info["seed_color"]) if fixed_phase is None else fixed_phase
    result: list[list[int]] = []
    for row in range(info["height"]):
        out_row: list[int] = []
        for col in range(info["width"]):
            dr, dc = abs(row - anchor[0]), abs(col - anchor[1])
            if metric == "manhattan":
                distance = dr + dc
            elif metric == "chebyshev":
                distance = max(dr, dc)
            else:
                raise ValueError(f"unknown metric: {metric}")
            out_row.append(CYCLE[(start + distance) % len(CYCLE)])
        result.append(out_row)
    return result


def competitor_is_ambiguous(competitor, demos, query) -> bool:
    fits = all(competitor(pair["input"]) == pair["output"] for pair in demos)
    return fits and competitor(query["input"]) != query["output"]
