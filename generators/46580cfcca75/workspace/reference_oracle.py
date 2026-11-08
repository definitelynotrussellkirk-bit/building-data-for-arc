"""Independent visible-grid oracle and rival probes for task 46580cfcca75.

This module intentionally does not import the selected generator.  It mirrors the
canonical Racket contract directly: find same-colour 4-connected components and
redraw each component's tight bounding-box perimeter on a blank grid.
"""
from __future__ import annotations


def objects(grid):
    """Return same-colour 4-connected components in row-major order."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == colour):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            found.append({
                "colour": colour,
                "cells": frozenset(cells),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return found


def _paint_outline(out, obj):
    r1, c1, r2, c2 = obj["bbox"]
    colour = obj["colour"]
    for r in range(r1, r2 + 1):
        out[r][c1] = colour
        out[r][c2] = colour
    for c in range(c1 + 1, c2):
        out[r1][c] = colour
        out[r2][c] = colour


def oracle(grid):
    out = [[0 for _ in row] for row in grid]
    for obj in objects(grid):
        _paint_outline(out, obj)
    return out


def identity(grid):
    return [list(row) for row in grid]


def largest_only(grid):
    out = [[0 for _ in row] for row in grid]
    objs = objects(grid)
    if objs:
        # Canonical object order breaks equal-area ties.
        obj = max(enumerate(objs), key=lambda item: (len(item[1]["cells"]), -item[0]))[1]
        _paint_outline(out, obj)
    return out


def drop_thin(grid):
    out = [[0 for _ in row] for row in grid]
    for obj in objects(grid):
        r1, c1, r2, c2 = obj["bbox"]
        if r2 - r1 + 1 >= 3 and c2 - c1 + 1 >= 3:
            _paint_outline(out, obj)
    return out


def global_bbox(grid):
    objs = objects(grid)
    out = [[0 for _ in row] for row in grid]
    if not objs:
        return out
    cells = [cell for obj in objs for cell in obj["cells"]]
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    # A deliberately wrong fixed-colour/global-object shortcut.
    fake = {
        "colour": objs[0]["colour"],
        "bbox": (min(rows), min(cols), max(rows), max(cols)),
    }
    _paint_outline(out, fake)
    return out


def facts(grid):
    objs = objects(grid)
    solid = []
    thin = 0
    visible = 0
    for obj in objs:
        r1, c1, r2, c2 = obj["bbox"]
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        solid.append(len(obj["cells"]) == bh * bw)
        thin += int(min(bh, bw) <= 2)
        visible += int(bh >= 3 and bw >= 3)
    return {
        "objects": len(objs),
        "solid": tuple(solid),
        "thin": thin,
        "visible": visible,
        "colours": tuple(obj["colour"] for obj in objs),
    }
