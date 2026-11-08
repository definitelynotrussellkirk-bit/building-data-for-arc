"""Visible-example local bridging hypothesis, with no reference-runtime imports."""
def solve(grid):
    if not isinstance(grid, list) or not grid or not grid[0]:
        raise ValueError("expected a nonempty grid")
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        raise ValueError("expected integer ARC colors")
    answer = [row[:] for row in grid]
    for r in range(height):
        for c in range(width):
            if grid[r][c]:
                continue
            proposals = set()
            if 0 < c < width-1 and grid[r][c-1] == grid[r][c+1] != 0:
                proposals.add(grid[r][c-1])
            if 0 < r < height-1 and grid[r-1][c] == grid[r+1][c] != 0:
                proposals.add(grid[r-1][c])
            if len(proposals) > 1:
                raise ValueError("conflicting-axis behavior is not identified by the visible examples")
            if proposals:
                answer[r][c] = next(iter(proposals))
    return answer
