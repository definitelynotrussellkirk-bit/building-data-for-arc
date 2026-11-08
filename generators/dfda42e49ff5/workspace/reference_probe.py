"""Independent probes for the reviewed dfda42e49ff5 generator.

The selected generator owns construction and declarations.  This module owns a
small, deliberately separate implementation of the task rule and the named
rivals used by tests and reviewer evidence.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable, Iterable

TASK_ID = "dfda42e49ff5"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | None = None):
    source = Path(path).resolve() if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def freeze(grid: Iterable[Iterable[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return same-color four-connected foreground components."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                rr, cc = current
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            found.append({"color": color, "cells": tuple(sorted(cells))})
    found.sort(key=lambda component: component["cells"][0])
    return found


def _fill_component_rows(output: list[list[int]], component: dict[str, Any]) -> None:
    by_row: dict[int, list[int]] = {}
    for row, column in component["cells"]:
        by_row.setdefault(row, []).append(column)
    for row, columns in by_row.items():
        for column in range(min(columns), max(columns) + 1):
            output[row][column] = component["color"]


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    for component in components(grid):
        _fill_component_rows(output, component)
    return output


def per_color_row_span(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: treat every color as one object, even when disconnected."""
    output = [list(row) for row in grid]
    by_color_row: dict[tuple[int, int], list[int]] = {}
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color:
                by_color_row.setdefault((color, row), []).append(column)
    for (color, row), columns in by_color_row.items():
        for column in range(min(columns), max(columns) + 1):
            output[row][column] = color
    return output


def largest_component_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: transform only the largest visible object."""
    output = [list(row) for row in grid]
    found = components(grid)
    if found:
        largest = max(found, key=lambda component: (len(component["cells"]), tuple(component["cells"])))
        _fill_component_rows(output, largest)
    return output


def component_bbox_fill(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: fill every component's full bounding rectangle."""
    output = [list(row) for row in grid]
    for component in components(grid):
        rows = [row for row, _ in component["cells"]]
        columns = [column for _, column in component["cells"]]
        for row in range(min(rows), max(rows) + 1):
            for column in range(min(columns), max(columns) + 1):
                output[row][column] = component["color"]
    return output


def component_global_right_span(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: extend every occupied object row to its global right edge."""
    output = [list(row) for row in grid]
    for component in components(grid):
        right = max(column for _, column in component["cells"])
        by_row: dict[int, list[int]] = {}
        for row, column in component["cells"]:
            by_row.setdefault(row, []).append(column)
        for row, columns in by_row.items():
            for column in range(min(columns), right + 1):
                output[row][column] = component["color"]
    return output


def one_cell_per_gap(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: repair only the first missing cell in each gappy row."""
    output = [list(row) for row in grid]
    for component in components(grid):
        cells = set(component["cells"])
        by_row: dict[int, list[int]] = {}
        for row, column in cells:
            by_row.setdefault(row, []).append(column)
        for row, columns in by_row.items():
            for column in range(min(columns), max(columns) + 1):
                if (row, column) not in cells:
                    output[row][column] = component["color"]
                    break
    return output


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "per_color_row_span": per_color_row_span,
    "largest_component_only": largest_component_only,
    "component_bbox_fill": component_bbox_fill,
    "component_global_right_span": component_global_right_span,
    "one_cell_per_gap": one_cell_per_gap,
}


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    found = components(grid)
    colors = {component["color"] for component in found}
    sizes = tuple(sorted(len(component["cells"]) for component in found))
    normalized = set()
    max_gap = 0
    for component in found:
        cells = component["cells"]
        min_row = min(row for row, _ in cells)
        min_column = min(column for _, column in cells)
        normalized.add(tuple(sorted((row - min_row, column - min_column) for row, column in cells)))
        by_row: dict[int, set[int]] = {}
        for row, column in cells:
            by_row.setdefault(row, set()).add(column)
        for columns in by_row.values():
            if len(columns) >= 2:
                max_gap = max(max_gap, max(columns) - min(columns) + 1 - len(columns))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "component_count": len(found),
        "color_count": len(colors),
        "component_sizes": sizes,
        "normalized_shapes": normalized,
        "max_gap": max_gap,
    }


COUNTEREXAMPLE = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 2, 0, 0, 2, 0, 0, 2, 0],
    [2, 2, 2, 2, 0, 0, 2, 2, 2, 2, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


GLOBAL_RIGHT_COUNTEREXAMPLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 2, 0, 0, 0],
    [0, 2, 2, 2, 2, 2, 2, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]
