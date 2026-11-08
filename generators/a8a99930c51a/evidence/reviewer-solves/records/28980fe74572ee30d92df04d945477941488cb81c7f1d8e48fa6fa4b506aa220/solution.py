"""Visible-example solution for a8a99930c51a."""


def solve(grid):
    """Cycle every body color through the nonzero row-0 codes, left to right."""
    if not grid:
        return []
    codes = [value for value in grid[0] if value != 0]
    if not codes:
        return [list(row) for row in grid]
    successor = {
        color: codes[(index + 1) % len(codes)]
        for index, color in enumerate(codes)
    }
    return [
        list(row) if r == 0 else [successor.get(value, value) for value in row]
        for r, row in enumerate(grid)
    ]
