"""Visible-example solution for reviewer-authored task 2a5919c40197."""


def solve(grid):
    """Paint each uniform row gray (5), and every mixed row black (0)."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    return [[5 if len(set(row)) == 1 else 0] * width for row in grid]
