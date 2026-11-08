"""Visible-example solution for the reviewer episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete the fourth corner implied by three equal nonzero cells."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if len(cells) != 3:
        raise ValueError(f"expected exactly three nonzero cells, found {len(cells)}")

    colors = {value for _, _, value in cells}
    rows = sorted({row for row, _, _ in cells})
    cols = sorted({col for _, col, _ in cells})
    if len(colors) != 1 or len(rows) != 2 or len(cols) != 2:
        raise ValueError("cells must share one color and span two rows and columns")

    present = {(row, col) for row, col, _ in cells}
    missing = [
        (row, col)
        for row in rows
        for col in cols
        if (row, col) not in present
    ]
    if len(missing) != 1:
        raise ValueError("expected exactly one missing rectangle corner")

    result = [list(row) for row in grid]
    row, col = missing[0]
    result[row][col] = next(iter(colors))
    return result
