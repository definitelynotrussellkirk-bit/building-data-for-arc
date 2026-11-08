"""Independent geometry oracle and probes for task eb92fce9b549.

This module deliberately does not import production helpers beyond the dynamic
loader.  Tests and the long-run semantic census use it to avoid checking the
sampler with its own implementation.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Iterable

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
TASK_ID = "eb92fce9b549"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | os.PathLike[str] | None = None) -> ModuleType:
    source = Path(path) if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("review_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decode_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def canonical_pairs() -> list[dict]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                pairs = row["train"] + row["test"]
                return [
                    {
                        "input": _decode_grid(pair["input"]),
                        "output": _decode_grid(pair["output"]),
                    }
                    for pair in pairs
                ]
    raise KeyError(f"canonical task {TASK_ID} not found in {path}")


def components(grid: list[list[int]]) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in CARDINAL:
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append((color, tuple(sorted(cells))))
    return result


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    r0, c0, r1, c1 = bbox(cells)
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def ranked_output(grid: list[list[int]], *, by: str = "bbox") -> list[list[int]]:
    """Independent implementation of the intended and rival ranking rules."""
    comps = components(grid)
    if by == "bbox":
        key = lambda item: (-bbox_area(item[1]), bbox(item[1]), item[1])
    elif by == "cells":
        key = lambda item: (-len(item[1]), -bbox_area(item[1]), bbox(item[1]), item[1])
    else:
        raise ValueError(f"unknown rank mode: {by}")
    ordered = sorted(comps, key=key)
    out = [[0 for _ in row] for row in grid]
    for rank, (_, cells) in enumerate(ordered, start=2):
        for row, col in cells:
            out[row][col] = rank
    return out


def observed(grid: list[list[int]]) -> dict[str, object]:
    comps = components(grid)
    colors = {color for color, _ in comps}
    if len(colors) != 1:
        raise ValueError(f"expected one foreground color, found {sorted(colors)}")
    return {
        "grid_size": len(grid),
        "n_objects": len(comps),
        "layout": "rings" if is_nested_rings(grid) else "scattered",
        "foreground_color": next(iter(colors)),
    }


def _is_perimeter(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    r0, c0, r1, c1 = bbox(cells)
    expected = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }
    return cells == expected


def is_nested_rings(grid: list[list[int]]) -> bool:
    comps = components(grid)
    if len(comps) < 2 or not all(_is_perimeter(cells) for _, cells in comps):
        return False
    ordered = sorted((bbox(cells) for _, cells in comps), key=lambda box: -((box[2]-box[0]+1)*(box[3]-box[1]+1)))
    for outer, inner in zip(ordered, ordered[1:]):
        if not (
            outer[0] + 1 < inner[0]
            and outer[1] + 1 < inner[1]
            and inner[2] + 1 < outer[2]
            and inner[3] + 1 < outer[3]
        ):
            return False
    return True
