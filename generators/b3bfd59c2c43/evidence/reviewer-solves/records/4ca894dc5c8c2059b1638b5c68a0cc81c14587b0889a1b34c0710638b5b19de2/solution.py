"""Visible-only solution for blind task b3bfd59c2c43."""


def solve(grid):
    """Recolor the four-neighbor boundary of every colored object to azure (8)."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        if len(row) != width:
            raise ValueError("grid must be rectangular")
        for c, color in enumerate(row):
            if color == 0:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if rr < 0 or rr >= height or cc < 0 or cc >= width or grid[rr][cc] != color:
                    out[r][c] = 8
                    break
    return out
