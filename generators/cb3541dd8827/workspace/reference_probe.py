"""Independent review oracle for cb3541dd8827.

The helper discovers arbitrary-colour rectangular-outline components directly
from pixels and implements the selected canonical transformation plus several
plausible shortcut rules.  It is test tooling only; Racket remains the label
authority used by the public checks.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Any, Callable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "cb3541dd8827"


def root() -> Path:
    return Path(find_root(__file__))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or root() / "generators" / TASK_ID / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=root(), labeled_only=True)


def _normal_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    rows = [list(row) if isinstance(row, (list, tuple)) else None for row in grid]
    if rows[0] is None or not rows[0]:
        raise ValueError("grid rows must be nonempty sequences")
    width = len(rows[0])
    if any(row is None or len(row) != width for row in rows):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in rows for value in row):
        raise ValueError("grid cells must be integer ARC colours")
    return rows  # type: ignore[return-value]


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": cells})
    return result


def frames(grid: Any) -> list[dict[str, Any]]:
    """Return every exact monochrome rectangular-outline component."""
    rows = _normal_grid(grid)
    found: list[dict[str, Any]] = []
    for component in _components(rows):
        cells = component["cells"]
        r1 = min(row for row, _ in cells)
        r2 = max(row for row, _ in cells)
        c1 = min(col for _, col in cells)
        c2 = max(col for _, col in cells)
        if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
            continue
        border = (
            {(r1, col) for col in range(c1, c2 + 1)}
            | {(r2, col) for col in range(c1, c2 + 1)}
            | {(row, c1) for row in range(r1, r2 + 1)}
            | {(row, c2) for row in range(r1, r2 + 1)}
        )
        if cells != border:
            continue
        frame_color = component["color"]
        interior = [
            (row, col)
            for row in range(r1 + 1, r2)
            for col in range(c1 + 1, c2)
        ]
        seed_cells = [
            (row, col)
            for row, col in interior
            if rows[row][col] not in (0, frame_color)
        ]
        seed_colors = sorted({rows[row][col] for row, col in seed_cells})
        found.append(
            {
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "frame_color": frame_color,
                "seed_cells": seed_cells,
                "seed_colors": seed_colors,
            }
        )
    return sorted(found, key=lambda item: (item["r1"], item["c1"], item["frame_color"]))


def _transform(grid: Any, chooser: Callable[[list[dict[str, Any]], int], int | None]) -> list[list[int]]:
    rows = _normal_grid(grid)
    parsed = frames(rows)
    out = deepcopy(rows)
    for index, frame in enumerate(parsed):
        fill = chooser(parsed, index)
        if fill is None:
            continue
        for row in range(frame["r1"] + 1, frame["r2"]):
            for col in range(frame["c1"] + 1, frame["c2"]):
                out[row][col] = fill
    return out


def intended_output(grid: Any) -> list[list[int]]:
    def choose(parsed: list[dict[str, Any]], index: int) -> int | None:
        seeds = parsed[index]["seed_colors"]
        return seeds[0] if len(seeds) == 1 else None

    return _transform(grid, choose)


def color_two_only_output(grid: Any) -> list[list[int]]:
    def choose(parsed: list[dict[str, Any]], index: int) -> int | None:
        frame = parsed[index]
        return frame["seed_colors"][0] if frame["frame_color"] == 2 and len(frame["seed_colors"]) == 1 else None

    return _transform(grid, choose)


def global_seed_output(grid: Any) -> list[list[int]]:
    parsed = frames(grid)
    global_seed = next(
        (frame["seed_colors"][0] for frame in parsed if len(frame["seed_colors"]) == 1),
        None,
    )
    return _transform(grid, lambda _parsed, _index: global_seed)


def first_frame_only_output(grid: Any) -> list[list[int]]:
    def choose(parsed: list[dict[str, Any]], index: int) -> int | None:
        seeds = parsed[index]["seed_colors"]
        return seeds[0] if index == 0 and len(seeds) == 1 else None

    return _transform(grid, choose)


def frame_color_output(grid: Any) -> list[list[int]]:
    return _transform(grid, lambda parsed, index: parsed[index]["frame_color"])


def observed(grid: Any) -> dict[str, Any]:
    rows = _normal_grid(grid)
    parsed = frames(rows)
    return {
        "grid_h": len(rows),
        "grid_w": len(rows[0]),
        "n_frames": len(parsed),
        "palette_size": len({value for row in rows for value in row}),
        "frame_colors": tuple(frame["frame_color"] for frame in parsed),
        "seed_colors": tuple(
            frame["seed_colors"][0] if len(frame["seed_colors"]) == 1 else None
            for frame in parsed
        ),
    }
