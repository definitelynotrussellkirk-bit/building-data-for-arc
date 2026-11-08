"""Independent authoring oracle and portable loader for task 54b040e4bd08."""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
from typing import Iterable

TASK_ID = "54b040e4bd08"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    candidate = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK_ID, root=find_root(__file__))


def infer_tile(grid: list[list[int]]) -> tuple[int, int, list[list[int]]]:
    """Mirror the selected Racket candidate order without importing production."""
    height, width = len(grid), len(grid[0])
    for period_r in range(1, min(5, height) + 1):
        for period_c in range(1, min(5, width) + 1):
            buckets = [[set() for _ in range(period_c)] for _ in range(period_r)]
            for row_index, row in enumerate(grid):
                for column_index, value in enumerate(row):
                    if value != 0:
                        buckets[row_index % period_r][column_index % period_c].add(value)
            if all(len(bucket) == 1 for row in buckets for bucket in row):
                tile = [[next(iter(bucket)) for bucket in row] for row in buckets]
                return period_r, period_c, tile
    raise ValueError("no complete periodic tile is inferable")


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    period_r, period_c, tile = infer_tile(grid)
    return [
        [value if value != 0 else tile[r % period_r][c % period_c]
         for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _line_period(values: Iterable[tuple[int, int]]) -> tuple[int, dict[int, int]] | None:
    observed = list(values)
    for period in range(1, 6):
        residues: dict[int, set[int]] = {index: set() for index in range(period)}
        for position, value in observed:
            if value != 0:
                residues[position % period].add(value)
        if all(len(bucket) == 1 for bucket in residues.values()):
            return period, {index: next(iter(bucket)) for index, bucket in residues.items()}
    return None


def row_only_output(grid: list[list[int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        inferred = _line_period(enumerate(row))
        if inferred is None:
            continue
        period, values = inferred
        for c, value in enumerate(row):
            if value == 0:
                out[r][c] = values[c % period]
    return out


def column_only_output(grid: list[list[int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for c in range(width):
        inferred = _line_period((r, grid[r][c]) for r in range(height))
        if inferred is None:
            continue
        period, values = inferred
        for r in range(height):
            if grid[r][c] == 0:
                out[r][c] = values[r % period]
    return out


def top_left_output(grid: list[list[int]]) -> list[list[int]]:
    period_r, period_c, _ = infer_tile(grid)
    tile = [row[:period_c] for row in grid[:period_r]]
    return [
        [value if value != 0 else tile[r % period_r][c % period_c]
         for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def observed(grid: list[list[int]]) -> dict[str, object]:
    period_r, period_c, _ = infer_tile(grid)
    zeros = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0]
    if not zeros:
        raise ValueError("missing zero hole")
    rows = [point[0] for point in zeros]
    cols = [point[1] for point in zeros]
    top, left = min(rows), min(cols)
    bottom, right = max(rows), max(cols)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "tile_shape": f"{period_r}x{period_c}",
        "vertical_margin": top,
        "horizontal_margin": left,
        "hole_h": bottom - top + 1,
        "hole_w": right - left + 1,
    }
