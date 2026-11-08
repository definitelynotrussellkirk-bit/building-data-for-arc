"""Complete both reflections of the visible seed pattern."""


def solve(grid):
    h, w = len(grid), len(grid[0])
    result = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0:
                continue
            for rr in (r, h - 1 - r):
                for cc in (c, w - 1 - c):
                    result[rr][cc] = color
    return result
