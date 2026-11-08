"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations

from collections import Counter, deque


def _components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            min_r = min(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            max_r = max(r for r, _ in cells)
            max_c = max(c for _, c in cells)
            normalized = tuple(sorted((r - min_r, c - min_c) for r, c in cells))
            result.append(
                {
                    "cells": set(cells),
                    "bbox": (min_r, min_c, max_r, max_c),
                    "norm": normalized,
                }
            )
    return sorted(result, key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))


def solve(grid):
    objects = _components(grid)
    counts = Counter(obj["norm"] for obj in objects)
    winner = max(counts, key=lambda shape: counts[shape])
    selected = next(obj for obj in objects if obj["norm"] == winner)
    min_r, min_c, max_r, max_c = selected["bbox"]
    return [
        [8 if (row, col) in selected["cells"] else 0 for col in range(min_c, max_c + 1)]
        for row in range(min_r, max_r + 1)
    ]
