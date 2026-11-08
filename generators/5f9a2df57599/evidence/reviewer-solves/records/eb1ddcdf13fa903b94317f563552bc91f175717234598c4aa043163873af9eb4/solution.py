"""Visible-example solution: fill zero cells inside complete gray rectangles."""

def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for top in range(h - 2):
        for bottom in range(top + 2, h):
            for left in range(w - 2):
                if not all(grid[r][left] == 5 for r in range(top, bottom + 1)):
                    continue
                for right in range(left + 2, w):
                    if not all(grid[top][c] == grid[bottom][c] == 5
                               for c in range(left, right + 1)):
                        continue
                    if not all(grid[r][right] == 5 for r in range(top, bottom + 1)):
                        continue
                    for r in range(top + 1, bottom):
                        for c in range(left + 1, right):
                            if grid[r][c] == 0:
                                out[r][c] = 4
    return out
