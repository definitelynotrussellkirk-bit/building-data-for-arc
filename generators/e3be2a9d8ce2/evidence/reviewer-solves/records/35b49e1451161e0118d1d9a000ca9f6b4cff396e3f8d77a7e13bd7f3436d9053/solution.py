"""Infer corner-facing L extensions from the visible demonstrations only."""

def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0:
                continue
            # The examples place seeds on diagonals entering from a corner.
            r_edge = 0 if r < height - 1 - r else height - 1
            c_edge = 0 if c < width - 1 - c else width - 1
            for rr in range(min(r, r_edge), max(r, r_edge) + 1):
                result[rr][c] = color
            for cc in range(min(c, c_edge), max(c, c_edge) + 1):
                result[r][cc] = color
    return result
