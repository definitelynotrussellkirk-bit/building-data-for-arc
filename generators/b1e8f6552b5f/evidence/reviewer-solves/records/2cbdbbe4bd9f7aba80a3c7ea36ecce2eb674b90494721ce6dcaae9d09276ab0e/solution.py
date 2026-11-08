def solve(grid):
    """Replace each nonzero marker with a same-color hollow 3x3 ring."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color == 0:
                continue
            for drow in (-1, 0, 1):
                for dcol in (-1, 0, 1):
                    if drow == 0 and dcol == 0:
                        continue
                    rr, cc = row + drow, col + dcol
                    if 0 <= rr < height and 0 <= cc < width:
                        out[rr][cc] = color
    return out
