"""Visible-example solution for the reviewer-authored ARC episode."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def solve(grid):
    objects = [
        {"color": color, "shape": _normalize(cells), "cells": cells}
        for color, cells in _components(grid)
    ]
    if not objects:
        return []

    max_size = max(len(obj["shape"]) for obj in objects)
    full_shapes = [obj["shape"] for obj in objects if len(obj["shape"]) == max_size]
    canonical = full_shapes[0]

    defective = [
        obj
        for obj in objects
        if len(obj["shape"]) < max_size and obj["shape"] < canonical
    ]
    if len(defective) != 1:
        raise ValueError(f"expected one defective strict subset, found {len(defective)}")

    color = defective[0]["color"]
    height = max(r for r, _ in canonical) + 1
    width = max(c for _, c in canonical) + 1
    return [
        [color if (r, c) in canonical else 0 for c in range(width)]
        for r in range(height)
    ]
