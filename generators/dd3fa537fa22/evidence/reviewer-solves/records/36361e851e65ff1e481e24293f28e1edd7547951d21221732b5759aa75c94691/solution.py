"""Visible-example solution for ARC task dd3fa537fa22."""
from __future__ import annotations


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    out = []
    for sr in range(height):
        for sc in range(width):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            cells = set()
            stack = [(sr, sc)]
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            out.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return out


def _complete_frame(component):
    if component["color"] != 8:
        return None
    r1, c1, r2, c2 = component["bbox"]
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return None
    perimeter = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    if component["cells"] != perimeter:
        return None
    return {
        **component,
        "shape": (r2 - r1 - 1, c2 - c1 - 1),
    }


def _solid_insert(component):
    if component["color"] in (0, 8):
        return None
    r1, c1, r2, c2 = component["bbox"]
    rectangle = {
        (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
    }
    if component["cells"] != rectangle:
        return None
    return {
        **component,
        "shape": (r2 - r1 + 1, c2 - c1 + 1),
    }


def solve(grid):
    height, width = len(grid), len(grid[0])
    components = _components(grid)
    frames = [frame for item in components if (frame := _complete_frame(item))]
    inserts = [insert for item in components if (insert := _solid_insert(item))]

    result = [[0 for _ in range(width)] for _ in range(height)]
    for frame in frames:
        for r, c in frame["cells"]:
            result[r][c] = 8

    for insert in inserts:
        frame = next(
            (candidate for candidate in frames if candidate["shape"] == insert["shape"]),
            None,
        )
        if frame is None:
            continue
        r1, c1, r2, c2 = frame["bbox"]
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                result[r][c] = insert["color"]
    return result
