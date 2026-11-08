"""Independent parser, oracle, and shortcut probes for task 27b865c5f43a.

This module intentionally does not import production helpers from generator.py.
It is a reusable review tool: future agents can inspect the input grammar,
calculate labels, and reproduce the two canonical-fitting ordering shortcuts
without trusting the implementation under review.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
from typing import Any, Callable

TASK_ID = "27b865c5f43a"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    target = Path(path) if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"reviewed_generator_{TASK_ID}", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs as _canonical_pairs, find_root

    return _canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty row sequence")
    if any(not isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("every row must be a sequence")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def components(grid: Any) -> list[dict[str, Any]]:
    """Return same-color 4-connected components, matching Racket ``objects``."""
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    rr, cc = point
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and point not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            found.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                    "size": len(cells),
                }
            )
    return found


def binary_crop(component: dict[str, Any]) -> list[list[int]]:
    r0, c0, r1, c1 = component["bbox"]
    crop = [[0 for _ in range(c1 - c0 + 1)] for _ in range(r1 - r0 + 1)]
    for row, col in component["cells"]:
        crop[row - r0][col - c0] = 1
    return crop


def _gallery_for_order(grid: Any, key: Callable[[dict[str, Any]], Any]) -> list[list[int]]:
    objects = sorted(components(grid), key=key)
    if not objects:
        raise ValueError("gallery needs at least one object")
    shapes = [binary_crop(obj) for obj in objects]
    panel_h = max(len(shape) for shape in shapes)
    panel_w = max(len(shape[0]) for shape in shapes)
    padded = []
    for shape in shapes:
        panel = [[0] * panel_w for _ in range(panel_h)]
        for row, values in enumerate(shape):
            for col, value in enumerate(values):
                panel[row][col] = value
        padded.append(panel)
    count = len(padded)
    out_h = count * panel_h + count - 1
    out_w = count * panel_w + count - 1
    out = [[0] * out_w for _ in range(out_h)]
    for gallery_row, first in enumerate(padded):
        for gallery_col, second in enumerate(padded):
            top = gallery_row * (panel_h + 1)
            left = gallery_col * (panel_w + 1)
            for row in range(panel_h):
                for col in range(panel_w):
                    if first[row][col] or second[row][col]:
                        out[top + row][left + col] = 8
    return out


def rule_output(grid: Any) -> list[list[int]]:
    """Intended rule: left-column order, then top-row tie break."""
    return _gallery_for_order(grid, lambda obj: (obj["bbox"][1], obj["bbox"][0]))


def color_sorted_output(grid: Any) -> list[list[int]]:
    """Canonical-fitting rival: order objects by their source color."""
    return _gallery_for_order(grid, lambda obj: (obj["color"], obj["bbox"][1], obj["bbox"][0]))


def row_sorted_output(grid: Any) -> list[list[int]]:
    """Canonical-fitting rival: order objects top-to-bottom, then left-to-right."""
    return _gallery_for_order(grid, lambda obj: (obj["bbox"][0], obj["bbox"][1]))


def observed(grid: Any) -> dict[str, Any]:
    """Independently decode every public axis from a generated input."""
    height, width = _validate_grid(grid)
    objects = sorted(components(grid), key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
    if len(objects) != 3:
        raise ValueError(f"expected three components, got {len(objects)}")

    palettes = {
        (2, 3, 4): "ascending",
        (2, 5, 8): "mixed",
        (7, 2, 5): "permuted",
        (9, 6, 1): "descending",
    }
    palette = tuple(obj["color"] for obj in objects)
    if palette not in palettes:
        raise ValueError(f"unrecognized generated palette {palette}")

    signatures = {
        (4, 4, 4): "sparse",
        (4, 5, 6): "mixed",
        (6, 7, 8): "dense",
    }
    sizes = tuple(obj["size"] for obj in objects)
    if sizes not in signatures:
        raise ValueError(f"unrecognized generated shape sizes {sizes}")

    top_rows = tuple(obj["bbox"][0] for obj in objects)
    minimum = min(top_rows)
    relative = tuple(value - minimum for value in top_rows)
    row_patterns = {
        (0, 0, 0): "aligned",
        (2, 1, 0): "reverse",
        (1, 0, 1): "valley",
        (0, 1, 0): "peak",
    }
    if relative not in row_patterns:
        raise ValueError(f"unrecognized generated row pattern {relative}")

    return {
        "grid_h": height,
        "grid_w": width,
        "palette_kind": palettes[palette],
        "shape_set": signatures[sizes],
        "row_pattern": row_patterns[relative],
    }


def color_order_conflict(grid: Any) -> bool:
    objects = sorted(components(grid), key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
    return [obj["color"] for obj in objects] != sorted(obj["color"] for obj in objects)


def row_order_conflict(grid: Any) -> bool:
    by_column = sorted(components(grid), key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
    by_row = sorted(components(grid), key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    return [obj["cells"] for obj in by_column] != [obj["cells"] for obj in by_row]


def retained_degenerate_inputs() -> dict[str, list[list[int]]]:
    """Load the exact invalid inputs retained with this review."""
    import json

    path = (
        HOME
        / "counterexamples"
        / "review-fa7d98e55ec14764"
        / "ordering-degenerates.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["cases"]
