#!/usr/bin/env python3
"""Independent oracle and probes for generator d8d37830884c.

The selected Racket program remains authoritative.  This module deliberately
reimplements the visible component-size transformation and the strongest
canonical-fitting colour shortcut without importing generator helpers.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "d8d37830884c"
HOME = Path(__file__).resolve().parents[1]
Cell = tuple[int, int]
Grid = list[list[int]]


def load_generator(path: str | None = None):
    selected = Path(path).resolve() if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"review_generator_{TASK_ID}", selected
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(
        TASK_ID,
        root=find_root(__file__),
        labeled_only=True,
    )


def _validate_grid(grid: Any) -> Grid:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("cells must be integer ARC colours 0..9")
    return [list(row) for row in grid]


def components(grid: Any) -> list[dict[str, Any]]:
    """Same-colour 4-connected nonzero objects, matching ``objects grid 0``."""
    normalized = _validate_grid(grid)
    height, width = len(normalized), len(normalized[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            colour = normalized[start_row][start_col]
            if colour == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[Cell] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and normalized[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            result.append(
                {
                    "colour": colour,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def rule_output(grid: Any) -> Grid:
    """Independent mirror: six-cell objects red(2), every other object blue(1)."""
    normalized = _validate_grid(grid)
    output = [[0] * len(normalized[0]) for _ in normalized]
    for component in components(normalized):
        colour = 2 if component["size"] == 6 else 1
        for row, col in component["cells"]:
            output[row][col] = colour
    return output


def gray_only_size_six_output(grid: Any) -> Grid:
    """Canonical-fitting rival: only gray(5) six-cell objects become red."""
    normalized = _validate_grid(grid)
    output = [[0] * len(normalized[0]) for _ in normalized]
    for component in components(normalized):
        colour = (
            2
            if component["size"] == 6 and component["colour"] == 5
            else 1
        )
        for row, col in component["cells"]:
            output[row][col] = colour
    return output


def observed(grid: Any) -> dict[str, int]:
    normalized = _validate_grid(grid)
    found = components(normalized)
    six = [component for component in found if component["size"] == 6]
    other = [component for component in found if component["size"] != 6]
    six_colours = {component["colour"] for component in six}
    other_colours = {component["colour"] for component in other}
    if len(six_colours) != 1 or len(other_colours) != 1:
        raise ValueError("each size group must use one recoverable colour")
    return {
        "grid_h": len(normalized),
        "grid_w": len(normalized[0]),
        "n_size6": len(six),
        "n_other": len(other),
        "size6_color": next(iter(six_colours)),
        "other_color": next(iter(other_colours)),
    }


def palette_profile(grid: Any) -> tuple[int, int, int]:
    normalized = _validate_grid(grid)
    return (
        len(normalized),
        len(normalized[0]),
        len({value for row in normalized for value in row}),
    )


def racket_outputs(grids: Iterable[Grid]) -> list[Grid]:
    """Apply the selected canonical Racket authority through the public API."""
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import apply_rule

    grids = [deepcopy(grid) for grid in grids]
    report = apply_rule(
        Catalog(find_root(__file__)),
        TASK_ID,
        grids,
        reference="canonical",
        timeout=240,
    )
    failures = [
        result for result in report["results"] if result.get("error") is not None
    ]
    if failures:
        raise RuntimeError(f"Racket apply failures: {failures}")
    return [result["output"] for result in report["results"]]
