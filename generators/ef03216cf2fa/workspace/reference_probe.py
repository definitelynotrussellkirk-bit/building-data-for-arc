"""Independent semantic oracle and coverage probe for ef03216cf2fa.

This reviewer-side helper intentionally does not import implementation helpers
from the selected generator.  It can therefore catch a shared bug in the
sampler's Python mirror instead of merely restating it.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
from typing import Callable

TASK_ID = "ef03216cf2fa"
RANK_LAYOUTS = ("ascending", "descending", "interleaved")


def _root() -> Path:
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "shared" / "runtime" / "reviewer_support.py").is_file():
            return parent
        if (parent / "reviewer_support.py").is_file() and (parent / "puzzle_generators").is_dir():
            return parent
    raise RuntimeError("could not locate staged or source repository root")


ROOT = _root()
for candidate in (ROOT / "shared" / "runtime", ROOT):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def load_generator(path: str | os.PathLike[str] | None = None):
    if path is None:
        path = os.environ.get("GENERATOR_UNDER_TEST")
    if path is None:
        source = ROOT / "generators" / TASK_ID / "generator.py"
        if not source.is_file():
            source = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    else:
        source = Path(path)
    source = source.resolve()
    spec = importlib.util.spec_from_file_location("reviewed_ef03216cf2fa", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _validate_rectangular(grid) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer colors 0..9")
    return len(grid), width


def components(grid: list[list[int]]) -> list[dict]:
    """Return same-color 4-connected nonzero objects in row-major order."""
    h, w = _validate_rectangular(grid)
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(r for r, _ in cells)
            r1 = max(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            c1 = max(c for _, c in cells)
            crop = [values[c0 : c1 + 1] for values in grid[r0 : r1 + 1]]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (r0, c0, r1, c1),
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "perimeter": 2 * ((r1 - r0 + 1) + (c1 - c0 + 1)),
                    "crop": crop,
                }
            )
    return result


def rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotate_counterclockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _pack(grid: list[list[int]], rotate_tall: Callable[[list[list[int]]], list[list[int]]]) -> list[list[int]]:
    items = []
    for obj in components(grid):
        shape = obj["crop"]
        if obj["height"] > obj["width"]:
            shape = rotate_tall(shape)
        r0, c0, _, _ = obj["bbox"]
        items.append((obj["perimeter"], r0, c0, shape))
    if not items:
        raise ValueError("input has no nonzero objects")
    items.sort(key=lambda item: (-item[0], item[1], item[2]))
    shapes = [item[3] for item in items]
    out_h = sum(len(shape) for shape in shapes) + len(shapes) - 1
    out_w = max(len(shape[0]) for shape in shapes)
    out = [[0 for _ in range(out_w)] for _ in range(out_h)]
    top = 0
    for shape in shapes:
        for r, row in enumerate(shape):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][c] = value
        top += len(shape) + 1
    return out


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    return _pack(grid, rotate_clockwise)


def counterclockwise_output(grid: list[list[int]]) -> list[list[int]]:
    return _pack(grid, rotate_counterclockwise)


def _rank_layout(perimeters: list[int]) -> str:
    if len(set(perimeters)) != len(perimeters):
        return "tied"
    ordered = sorted(perimeters)
    ranks = [ordered.index(value) for value in perimeters]
    if ranks == list(range(len(ranks))):
        return "ascending"
    if ranks == list(reversed(range(len(ranks)))):
        return "descending"
    return "interleaved"


def _palette_family(colors: set[int]) -> str:
    if colors and max(colors) <= 4:
        return "low"
    if colors and min(colors) >= 6:
        return "high"
    return "mixed"


def observed(grid: list[list[int]]) -> dict:
    objects = components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n": len(objects),
        "tall_count": sum(obj["height"] > obj["width"] for obj in objects),
        "rank_layout": _rank_layout([obj["perimeter"] for obj in objects]),
        "palette_family": _palette_family({obj["color"] for obj in objects}),
        "perimeters": [obj["perimeter"] for obj in objects],
        "colors": [obj["color"] for obj in objects],
    }


def canonical_counterclockwise_fit() -> bool:
    return all(counterclockwise_output(pair["input"]) == pair["output"] for pair in canonical_pairs())
