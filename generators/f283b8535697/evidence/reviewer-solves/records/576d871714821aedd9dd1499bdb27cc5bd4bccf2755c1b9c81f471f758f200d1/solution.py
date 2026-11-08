from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recover the rectangle hidden by 1s using top/bottom mirror symmetry."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    masked = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == 1
    ]
    if not masked:
        raise ValueError("expected a rectangular region marked with color 1")

    top = min(row for row, _ in masked)
    bottom = max(row for row, _ in masked)
    left = min(col for _, col in masked)
    right = max(col for _, col in masked)

    expected = (bottom - top + 1) * (right - left + 1)
    if len(masked) != expected:
        raise ValueError("the color-1 mask is not a filled rectangle")

    return [
        [grid[height - 1 - row][col] for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]
