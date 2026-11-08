"""Visible-example solution for ARC task 4fd85612056f."""
from __future__ import annotations

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the nonzero 4-connected component with the greatest row span.

    The visible examples use color-agnostic connectivity: touching nonzero
    cells remain one object even when their colors differ.  Deterministic
    secondary keys make the function total without changing any visible case.
    """
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in CARDINAL:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] == 0:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            components.append(cells)

    if not components:
        return [[0]]

    def bounds(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return min(rows), max(rows), min(cols), max(cols)

    def key(cells: list[tuple[int, int]]) -> tuple[int, int, int]:
        top, bottom, left, _ = bounds(cells)
        return bottom - top + 1, len(cells), -left

    winner = max(components, key=key)
    top, bottom, left, right = bounds(winner)
    occupied = set(winner)
    return [
        [grid[r][c] if (r, c) in occupied else 0 for c in range(left, right + 1)]
        for r in range(top, bottom + 1)
    ]
