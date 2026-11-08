from __future__ import annotations

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
SHIFTS = (
    (0, 0), (0, -1), (0, 1), (-1, 0), (1, 0),
    (-1, -1), (-1, 1), (1, -1), (1, 1),
    (0, -2), (0, 2), (-2, 0), (2, 0),
)


def _split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    starts = [0] + [c + 1 for c in separators]
    ends = separators + [w]
    return [[row[a:b] for row in grid] for a, b in zip(starts, ends) if a < b]


def _components(panel: list[list[int]]) -> list[dict]:
    h, w = len(panel), len(panel[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = panel[r][c]
            if color == 8 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and panel[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append({"color": color, "cells": tuple(sorted(cells)), "size": len(cells)})
    return found


def solve(grid: list[list[int]]) -> list[list[int]]:
    panels = _split_panels(grid)
    h = len(grid)
    w = len(panels[0][0])
    selected = [max(_components(panel), key=lambda item: item["size"]) for panel in panels]

    occupied: dict[tuple[int, int], int] = {}
    for obj in sorted(selected, key=lambda item: item["size"], reverse=True):
        for dr, dc in SHIFTS:
            shifted = [(r + dr, c + dc) for r, c in obj["cells"]]
            if all(0 <= r < h and 0 <= c < w and (r, c) not in occupied
                   for r, c in shifted):
                for cell in shifted:
                    occupied[cell] = obj["color"]
                break
    return [[occupied.get((r, c), 8) for c in range(w)] for r in range(h)]
