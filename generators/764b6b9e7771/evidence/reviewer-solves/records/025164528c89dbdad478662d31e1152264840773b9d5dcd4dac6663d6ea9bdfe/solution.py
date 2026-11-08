from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Trace the colored beam shown by the visible demonstrations."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    red = []
    blue = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                red.append((r, c))
            elif value == 1:
                blue.append((r, c))
    if len(red) != 1 or len(blue) != 1:
        return [list(row) for row in grid]

    r, c = red[0]
    br, bc = blue[0]
    dr, dc = br - r, bc - c
    if (dr, dc) not in {(1, 0), (-1, 0), (0, 1), (0, -1)}:
        return [list(row) for row in grid]

    height, width = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    visited: set[tuple[int, int, int, int]] = set()

    while True:
        state = (r, c, dr, dc)
        if state in visited:
            break
        visited.add(state)

        nr, nc = r + dr, c + dc
        if not (0 <= nr < height and 0 <= nc < width):
            break
        cell = grid[nr][nc]
        if cell == 5:
            break
        if cell == 0:
            out[nr][nc] = 8
        elif cell == 4:
            dr, dc = -dc, -dr
        elif cell == 6:
            dr, dc = dc, dr
        r, c = nr, nc

    return out
