"""Visible-example hypothesis: fill seeded rectangular yellow frames."""

def solve(grid):
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for top in range(height - 2):
        for left in range(width - 2):
            if grid[top][left] != 4:
                continue
            for bottom in range(top + 2, height):
                if grid[bottom][left] != 4:
                    continue
                for right in range(left + 2, width):
                    if not (all(grid[top][c] == grid[bottom][c] == 4 for c in range(left, right + 1))
                            and all(grid[r][left] == grid[r][right] == 4 for r in range(top, bottom + 1))):
                        continue
                    interior = [grid[r][c] for r in range(top + 1, bottom) for c in range(left + 1, right)]
                    if 4 in interior:
                        continue
                    seeds = set(interior) - {0}
                    if len(seeds) == 1:
                        color = next(iter(seeds))
                        for r in range(top + 1, bottom):
                            for c in range(left + 1, right):
                                out[r][c] = color
    return out
