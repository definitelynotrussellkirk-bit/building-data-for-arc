from __future__ import annotations


def solve(grid):
    """Tile the upper-left nonzero bounding rectangle over the full canvas."""
    height = len(grid)
    width = len(grid[0])
    nonzero = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not nonzero:
        return [list(row) for row in grid]

    motif_height = max(row for row, _ in nonzero) + 1
    motif_width = max(col for _, col in nonzero) + 1
    motif = [list(row[:motif_width]) for row in grid[:motif_height]]
    return [
        [motif[row % motif_height][col % motif_width] for col in range(width)]
        for row in range(height)
    ]
