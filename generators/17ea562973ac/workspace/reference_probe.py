"""Independent oracle and audit helpers for ARC task 17ea562973ac.

This module intentionally does not import geometry helpers from the production
``generator.py``.  Future reviewers can use it to test a candidate generator,
inspect exact public-axis observations, and compare plausible wrong rules.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Any

from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
)

TASK = "17ea562973ac"
ROOT = find_root(__file__)
CANONICAL_LEDGER = canonical_path(ROOT)
HOME = next(
    candidate
    for candidate in (
        ROOT / "generators" / TASK,
        ROOT / "puzzle_generators" / "per_puzzle" / TASK,
    )
    if (candidate / "generator.py").is_file()
)
DEFAULT_GENERATOR = HOME / "generator.py"


def load_generator(path: str | Path | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR)).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_17ea562973ac", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    # Resolve through the nearest source/runtime tree so copied task tests never
    # read a canonical ledger from an enclosing checkout.
    if canonical_path(ROOT) != CANONICAL_LEDGER:
        raise RuntimeError("canonical ledger changed during this process")
    return load_canonical_pairs(TASK, root=ROOT, labeled_only=True)


def facts(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be non-empty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be non-empty")
    width = len(grid[0])
    clean: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError("grid must be rectangular")
        converted: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("cells must be integer ARC colors 0..9")
            converted.append(value)
        clean.append(converted)

    cells = [(r, c, value) for r, row in enumerate(clean)
             for c, value in enumerate(row) if value != 0]
    if not cells:
        raise ValueError("at least one nonzero cell is required")
    colors = {value for _, _, value in cells}
    if len(colors) != 1:
        raise ValueError("all nonzero cells must have one color")
    rows = [r for r, _, _ in cells]
    cols = [c for _, c, _ in cells]
    bbox = (min(rows), min(cols), max(rows), max(cols))
    first_two = cells[:2]
    first_two_bbox = None
    if len(first_two) == 2:
        first_two_bbox = (
            min(first_two[0][0], first_two[1][0]),
            min(first_two[0][1], first_two[1][1]),
            max(first_two[0][0], first_two[1][0]),
            max(first_two[0][1], first_two[1][1]),
        )
    r1, c1, r2, c2 = bbox
    interior = any(r1 < r < r2 and c1 < c < c2 for r, c, _ in cells)
    return {
        "grid": clean,
        "grid_h": len(clean),
        "grid_w": width,
        "color": next(iter(colors)),
        "num_cells": len(cells),
        "cells": tuple((r, c) for r, c, _ in cells),
        "bbox": bbox,
        "first_two_bbox": first_two_bbox,
        "has_interior_marker": interior,
    }


def observed(grid: Any) -> dict[str, int]:
    info = facts(grid)
    return {key: info[key] for key in ("grid_h", "grid_w", "color", "num_cells")}


def _frame(shape: tuple[int, int], bbox: tuple[int, int, int, int], color: int) -> list[list[int]]:
    h, w = shape
    output = [[0 for _ in range(w)] for _ in range(h)]
    r1, c1, r2, c2 = bbox
    for c in range(c1, c2 + 1):
        output[r1][c] = color
        output[r2][c] = color
    for r in range(r1 + 1, r2):
        output[r][c1] = color
        output[r][c2] = color
    return output


def reference_output(grid: Any) -> list[list[int]]:
    info = facts(grid)
    return _frame((info["grid_h"], info["grid_w"]), info["bbox"], info["color"])


def retain_markers_output(grid: Any) -> list[list[int]]:
    info = facts(grid)
    output = deepcopy(info["grid"])
    frame = _frame((info["grid_h"], info["grid_w"]), info["bbox"], info["color"])
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value:
                output[r][c] = value
    return output


def first_two_output(grid: Any) -> list[list[int]]:
    info = facts(grid)
    if info["num_cells"] < 2:
        return deepcopy(info["grid"])
    return _frame(
        (info["grid_h"], info["grid_w"]),
        info["first_two_bbox"],
        info["color"],
    )


def at_least_three_output(grid: Any) -> list[list[int]]:
    info = facts(grid)
    if info["num_cells"] < 3:
        return deepcopy(info["grid"])
    return reference_output(grid)


def semantic_profile(grid: Any) -> dict[str, bool]:
    info = facts(grid)
    return {
        "two_markers": info["num_cells"] == 2,
        "interior_marker": info["has_interior_marker"],
        "first_two_incomplete": info["first_two_bbox"] != info["bbox"],
    }
