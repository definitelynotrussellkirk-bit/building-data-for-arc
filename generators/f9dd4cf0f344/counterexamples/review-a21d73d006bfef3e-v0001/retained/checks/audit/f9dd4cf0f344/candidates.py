"""Reviewed finite candidates for the public f9dd4cf0f344 lesson."""


def _copy(grid):
    return [row[:] for row in grid]


def intended(grid):
    out = _copy(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            color = grid[r - 1][c]
            if color != 0 and grid[r + 1][c] == color and grid[r][c - 1] == color and grid[r][c + 1] == color:
                out[r][c] = color
    return out


def overwrite_occupied(grid):
    out = _copy(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            color = grid[r - 1][c]
            if color != 0 and grid[r + 1][c] == color and grid[r][c - 1] == color and grid[r][c + 1] == color:
                out[r][c] = color
    return out


def cardinal_or_diagonal(grid):
    out = intended(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            color = grid[r - 1][c - 1]
            if color != 0 and grid[r - 1][c + 1] == color and grid[r + 1][c - 1] == color and grid[r + 1][c + 1] == color:
                out[r][c] = color
    return out


CANDIDATES = {
    "intended_empty_cardinal": intended,
    "overwrite_occupied": overwrite_occupied,
    "cardinal_or_diagonal": cardinal_or_diagonal,
}
