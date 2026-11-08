"""Solution inferred from this episode's visible examples; prior exposure disclosed."""

def solve(grid):
    out = [list(row) for row in grid]
    bar = next(r for r, row in enumerate(grid) if 1 in row)
    heights = {2: 4, 8: 3}
    for col, color in enumerate(grid[bar]):
        if color not in heights:
            continue
        height = heights[color]
        for offset in range(height):
            row = bar - height + offset
            if row >= 0:
                out[row][col] = color if offset == 0 else 1
    return out
