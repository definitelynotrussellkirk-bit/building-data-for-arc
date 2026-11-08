from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Reflect every colored source cell across the full-height 8 divider.

    Existing cells are retained except where a reflected source lands; reflected
    cells use the source color.  Reflections outside the grid are discarded.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_columns = [
        c for c in range(width) if all(grid[r][c] == 8 for r in range(height))
    ]
    if len(divider_columns) != 1:
        raise ValueError("expected exactly one full-height divider of color 8")
    axis = divider_columns[0]

    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c in range(axis):
            color = row[c]
            if color in (0, 8):
                continue
            reflected = 2 * axis - c
            if 0 <= reflected < width:
                output[r][reflected] = color
    return output
