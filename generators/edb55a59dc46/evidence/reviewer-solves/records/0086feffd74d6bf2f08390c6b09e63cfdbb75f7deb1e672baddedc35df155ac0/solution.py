from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Draw an alternating/cyclic cross centered on the unique 9 marker."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    marker_positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(marker_positions) != 1:
        raise ValueError("expected exactly one marker colored 9")
    marker_r, marker_c = marker_positions[0]

    key = [value for value in grid[0] if value not in (0, 9)]
    if not key:
        raise ValueError("expected at least one key color in the top row")

    result = [row[:] for row in grid]

    for c in range(width):
        if result[marker_r][c] == 0:
            distance = abs(c - marker_c)
            result[marker_r][c] = key[(distance - 1) % len(key)]

    for r in range(height):
        if result[r][marker_c] == 0:
            distance = abs(r - marker_r)
            result[r][marker_c] = key[(distance - 1) % len(key)]

    return result
