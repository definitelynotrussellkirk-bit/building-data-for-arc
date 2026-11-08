"""Independent probes for f4725b891d89 review tests.

This file intentionally does not import production rule helpers.  It gives future
reviewers a small oracle for the public row/column-intersection rule and portable
canonical-data access.
"""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Any

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "f4725b891d89"
TASK_HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None) -> ModuleType:
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def header_entries(grid: list[list[int]]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    top = [(c, grid[1][c]) for c in range(2, w - 1) if grid[1][c] not in (0, 5)]
    left = [(r, grid[r][1]) for r in range(2, h - 1) if grid[r][1] not in (0, 5)]
    return top, left


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    """Pure public-rule oracle: fill iff row and column labels are equal."""
    out = copy.deepcopy(grid)
    top, left = header_entries(grid)
    for row, row_color in left:
        for col, col_color in top:
            if row_color == col_color:
                out[row][col] = row_color
    return out


def observed_axes(grid: list[list[int]]) -> dict[str, int]:
    top, left = header_entries(grid)
    return {
        "frame_h": len(grid),
        "frame_w": len(grid[0]),
        "n_top_markers": len(top),
        "n_left_markers": len(left),
    }


def grid_profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({cell for row in grid for cell in row})
