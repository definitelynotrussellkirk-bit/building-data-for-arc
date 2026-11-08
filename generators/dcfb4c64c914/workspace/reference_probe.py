"""Independent Python probe for ARC task dcfb4c64c914.

This module intentionally does not import the task generator.  It mirrors the
published Racket authority closely enough to serve as an independent oracle in
portable task tests:

* split the input at full-height gray (5) separator columns;
* choose the largest 4-connected monochrome object in each of the first two
  panels (size, row peak, column peak, then top-left are tie-breakers);
* count object cells on each row of that object's own bounding box;
* pad the shorter profile with zeros, take absolute differences, and render a
  left-justified cyan (8) histogram.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable


Cell = tuple[int, int]
Grid = list[list[int]]


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty sequence of rows"
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return "every row must be a sequence"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return "grid values must be ARC color integers in 0..9"
    return None


def _components(panel: list[list[int]], *, col_offset: int) -> list[dict[str, Any]]:
    height = len(panel)
    width = len(panel[0]) if panel else 0
    seen: set[Cell] = set()
    objects: list[dict[str, Any]] = []
    for r in range(height):
        for c in range(width):
            color = panel[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            local_cells: list[Cell] = []
            while queue:
                rr, cc = queue.popleft()
                local_cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and panel[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            top = min(rr for rr, _ in local_cells)
            bottom = max(rr for rr, _ in local_cells)
            left_local = min(cc for _, cc in local_cells)
            right_local = max(cc for _, cc in local_cells)
            row_profile = tuple(
                sum(rr == row for rr, _ in local_cells)
                for row in range(top, bottom + 1)
            )
            col_profile = tuple(
                sum(cc == col for _, cc in local_cells)
                for col in range(left_local, right_local + 1)
            )
            shape = tuple(sorted((rr - top, cc - left_local) for rr, cc in local_cells))
            objects.append(
                {
                    "color": color,
                    "size": len(local_cells),
                    "top": top,
                    "bottom": bottom,
                    "left": left_local + col_offset,
                    "right": right_local + col_offset,
                    "height": bottom - top + 1,
                    "width": right_local - left_local + 1,
                    "profile": row_profile,
                    "col_profile": col_profile,
                    "shape": shape,
                    "local_cells": tuple(sorted(local_cells)),
                    "global_cells": tuple(sorted((rr, cc + col_offset) for rr, cc in local_cells)),
                }
            )
    return objects


def _largest(objects: Iterable[dict[str, Any]]) -> dict[str, Any]:
    candidates = list(objects)
    if not candidates:
        raise ValueError("panel has no non-background object")
    return min(
        candidates,
        key=lambda obj: (
            -obj["size"],
            -max(obj["profile"]),
            -max(obj["col_profile"]),
            obj["top"],
            obj["left"],
        ),
    )


def analyze(grid: Any) -> dict[str, Any]:
    """Return authority-oriented panel/object facts, or raise ``ValueError``."""
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    height = len(grid)
    width = len(grid[0])
    separators = [
        c for c in range(width) if all(grid[r][c] == 5 for r in range(height))
    ]
    bounds = [-1, *separators, width]
    spans = [
        (bounds[i] + 1, bounds[i + 1] - 1)
        for i in range(len(bounds) - 1)
        if bounds[i] + 1 <= bounds[i + 1] - 1
    ]
    if len(spans) < 2:
        raise ValueError("authority requires at least two nonempty vertical panels")

    panel_objects: list[list[dict[str, Any]]] = []
    for left, right in spans:
        panel = [list(row[left : right + 1]) for row in grid]
        panel_objects.append(_components(panel, col_offset=left))

    left_object = _largest(panel_objects[0])
    right_object = _largest(panel_objects[1])
    return {
        "height": height,
        "width": width,
        "separators": tuple(separators),
        "divider": separators[0] if len(separators) == 1 else None,
        "panel_spans": tuple(spans),
        "panel_objects": panel_objects,
        "left": left_object,
        "right": right_object,
    }


def histogram(profile: Iterable[int], *, color: int = 8) -> Grid:
    values = list(profile)
    if not values:
        return []
    width = max(1, max(values))
    return [[color if c < value else 0 for c in range(width)] for value in values]


def _difference(left: Iterable[int], right: Iterable[int]) -> list[int]:
    a = list(left)
    b = list(right)
    length = max(len(a), len(b))
    a.extend([0] * (length - len(a)))
    b.extend([0] * (length - len(b)))
    return [abs(a[index] - b[index]) for index in range(length)]


def authority_output(grid: Any) -> Grid:
    info = analyze(grid)
    return histogram(_difference(info["left"]["profile"], info["right"]["profile"]))


def canvas_aligned_output(grid: Any) -> Grid:
    """Plausible wrong rule: compare counts on absolute canvas rows."""
    info = analyze(grid)
    left = info["left"]
    right = info["right"]
    start = min(left["top"], right["top"])
    stop = max(left["bottom"], right["bottom"])
    left_counts = {row: 0 for row in range(start, stop + 1)}
    right_counts = {row: 0 for row in range(start, stop + 1)}
    for row, _ in left["global_cells"]:
        left_counts[row] += 1
    for row, _ in right["global_cells"]:
        right_counts[row] += 1
    return histogram(
        [abs(left_counts[row] - right_counts[row]) for row in range(start, stop + 1)]
    )


def bbox_span_output(grid: Any) -> Grid:
    """Plausible wrong rule: use each occupied row's horizontal span, not cell count."""
    info = analyze(grid)

    def spans(obj: dict[str, Any]) -> list[int]:
        by_row: dict[int, list[int]] = {}
        for row, col in obj["global_cells"]:
            by_row.setdefault(row, []).append(col)
        return [max(by_row[row]) - min(by_row[row]) + 1 for row in range(obj["top"], obj["bottom"] + 1)]

    return histogram(_difference(spans(info["left"]), spans(info["right"])))
