from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Combine the aligned panels around the full-width separator by occupancy OR."""
    separator = next(
        r for r, row in enumerate(grid)
        if row and len(set(row)) == 1 and row[0] != 0
    )
    panel_h = separator
    if len(grid) != 2 * panel_h + 1:
        raise ValueError("expected two equal-height panels around one separator row")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    return [
        [3 if grid[r][c] != 0 or grid[separator + 1 + r][c] != 0 else 0
         for c in range(width)]
        for r in range(panel_h)
    ]
