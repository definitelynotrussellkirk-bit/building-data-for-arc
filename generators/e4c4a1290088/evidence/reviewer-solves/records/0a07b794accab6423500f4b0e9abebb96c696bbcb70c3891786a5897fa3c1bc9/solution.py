from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete the equality table encoded by the first row and column.

    The top row contains column labels and the first column contains row labels.
    Each interior cell receives that label exactly when the row and column labels
    are the same; otherwise it remains background (0). The header row/column are
    preserved verbatim.
    """
    if not grid:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    out = [row[:] for row in grid]
    for r in range(1, len(grid)):
        row_label = grid[r][0]
        for c in range(1, width):
            col_label = grid[0][c]
            out[r][c] = row_label if row_label == col_label else 0
    return out
