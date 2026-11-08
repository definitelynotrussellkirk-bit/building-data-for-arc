"""Visible-example solution for blind task a178821cc6bf."""


def solve(grid):
    """Return 4 where aligned cells in both horizontal halves are background."""
    if not grid:
        return []

    width = len(grid[0])
    if width % 2:
        raise ValueError("input width must split into two equal halves")
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    half = width // 2
    return [
        [4 if row[col] == 0 and row[col + half] == 0 else 0 for col in range(half)]
        for row in grid
    ]
