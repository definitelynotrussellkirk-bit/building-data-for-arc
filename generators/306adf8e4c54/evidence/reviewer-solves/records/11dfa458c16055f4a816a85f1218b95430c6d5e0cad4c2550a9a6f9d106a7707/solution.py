from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Connect pairs of yellow (4) cells sharing a row or column.

    The visible examples preserve all existing cells and paint every zero cell
    between the leftmost/rightmost yellow in a row and between the topmost/
    bottommost yellow in a column.  The row/column spans are derived from the
    original input so newly painted cells do not create extra lines.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    original = [row[:] for row in grid]
    result = [row[:] for row in grid]

    for r, row in enumerate(original):
        cols = [c for c, value in enumerate(row) if value == 4]
        if len(cols) >= 2:
            for c in range(min(cols), max(cols) + 1):
                if result[r][c] == 0:
                    result[r][c] = 4

    for c in range(width):
        rows = [r for r in range(height) if original[r][c] == 4]
        if len(rows) >= 2:
            for r in range(min(rows), max(rows) + 1):
                if result[r][c] == 0:
                    result[r][c] = 4

    return result
