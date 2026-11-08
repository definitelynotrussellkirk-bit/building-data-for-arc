"""Independent parser, pixel oracle, and replay helpers for f7a512650552.

This file intentionally does not import production helpers from generator.py.
It is retained as a reusable review tool and as the oracle for task-local tests.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterable

TASK_ID = "f7a512650552"


def load_generator(path=None):
    path = Path(path or Path(__file__).resolve().parents[1] / "generator.py")
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _validate_grid(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer colors 0..9")


def _cells(panel):
    return {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}


def _row_close(cells: Iterable[tuple[int, int]]):
    cells = set(cells)
    rows = {}
    for r, c in cells:
        rows.setdefault(r, []).append(c)
    result = set(cells)
    for r, cols in rows.items():
        result.update((r, c) for c in range(min(cols), max(cols) + 1))
    return result


def _col_close(cells: Iterable[tuple[int, int]]):
    cells = set(cells)
    cols = {}
    for r, c in cells:
        cols.setdefault(c, []).append(r)
    result = set(cells)
    for c, rows in cols.items():
        result.update((r, c) for r in range(min(rows), max(rows) + 1))
    return result


def parse(grid):
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(separators) != 2:
        raise ValueError(f"expected two full color-5 columns, found {separators}")
    first, second = separators
    panels = (
        [row[:first] for row in grid],
        [row[first + 1 : second] for row in grid],
        [row[second + 1 :] for row in grid],
    )
    source, result, query = map(_cells, panels)
    row_result = _row_close(source)
    col_result = _col_close(source)
    if result == row_result:
        mode = 0
    elif result == col_result:
        mode = 1
    else:
        raise ValueError("worked result is neither source closure")
    return {
        "height": h,
        "width": w,
        "example_w": first,
        "query_w": w - second - 1,
        "mode": mode,
        "source": source,
        "result": result,
        "query": query,
        "row_source": row_result,
        "col_source": col_result,
        "panels": panels,
    }


def _crop(cells, color=8):
    cells = set(cells)
    if not cells:
        raise ValueError("cannot crop an empty object")
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [
        [color if (r, c) in cells else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]


def rule_output(grid):
    scene = parse(grid)
    transformed = _row_close(scene["query"]) if scene["mode"] == 0 else _col_close(scene["query"])
    return _crop(transformed, 8)


def opposite_mode_output(grid):
    scene = parse(grid)
    transformed = _col_close(scene["query"]) if scene["mode"] == 0 else _row_close(scene["query"])
    return _crop(transformed, 8)


def always_row_output(grid):
    return _crop(_row_close(parse(grid)["query"]), 8)


def always_column_output(grid):
    return _crop(_col_close(parse(grid)["query"]), 8)


def copy_query_output(grid):
    return _crop(parse(grid)["query"], 8)


def solid_bbox_output(grid):
    query = parse(grid)["query"]
    r1 = min(r for r, _ in query)
    r2 = max(r for r, _ in query)
    c1 = min(c for _, c in query)
    c2 = max(c for _, c in query)
    return [[8] * (c2 - c1 + 1) for _ in range(r2 - r1 + 1)]


def observed(grid):
    scene = parse(grid)
    return {
        "grid_h": scene["height"],
        "example_w": scene["example_w"],
        "query_w": scene["query_w"],
        "mode": scene["mode"],
    }


def palette_size(grid):
    return len({value for row in grid for value in row})
