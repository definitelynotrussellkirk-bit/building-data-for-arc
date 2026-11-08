"""Finite selector rivals used by the bounded teaching audit."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def _load_local(name, path):
    module_name = f"_01bdf9_rivals_{name}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


O = _load_local("oracle", HERE / "oracle.py")


def program_sources():
    return {
        "seed_frequency": (HERE / "seed_frequency_counterfactual.rkt").read_text(),
        "numeric_lowest": (HERE / "numeric_lowest.rkt").read_text(),
        "largest_total": (HERE / "largest_total.rkt").read_text(),
        "smallest_chamber_color": (HERE / "smallest_chamber_color.rkt").read_text(),
    }


def smallest_chamber_only(grid):
    filled = O.fill_all(grid)
    chamber = min(O.regions(grid), key=lambda cells: (len(cells), cells[0]))
    out = deepcopy(filled)
    for row, col in chamber:
        out[row][col] = 9
    return out


def independent_rectangles(grid):
    """Wrong total rival: infer divider lines and fill nominal rectangles."""
    height, width = len(grid), len(grid[0])
    h_lines = [
        row for row in range(1, height - 1)
        if sum(grid[row][col] == 5 for col in range(width)) >= width - 4
    ]
    v_lines = [
        col for col in range(1, width - 1)
        if sum(grid[row][col] == 5 for row in range(height)) >= height - 4
    ]
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    row_bounds = [0, *h_lines, height - 1]
    col_bounds = [0, *v_lines, width - 1]
    for top, bottom in zip(row_bounds, row_bounds[1:]):
        for left, right in zip(col_bounds, col_bounds[1:]):
            cells = [
                (row, col)
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
                if grid[row][col] != 5
            ]
            marker = next(
                (grid[row][col] for row, col in cells if grid[row][col] not in (0, 5)),
                0,
            )
            for row, col in cells:
                out[row][col] = marker
    return out


def python_outputs(grid):
    return {
        "smallest_chamber_only": smallest_chamber_only(grid),
        "independent_rectangles_fill": independent_rectangles(grid),
    }
