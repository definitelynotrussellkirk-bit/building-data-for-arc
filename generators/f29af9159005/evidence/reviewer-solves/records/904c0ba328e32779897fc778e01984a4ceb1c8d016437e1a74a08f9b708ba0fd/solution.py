def solve(grid):
    """Extend each red cell along four axes until a blue cell or the edge."""
    out = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 2:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                while 0 <= rr < height and 0 <= cc < width:
                    if grid[rr][cc] == 1:
                        break
                    if grid[rr][cc] == 0:
                        out[rr][cc] = 4
                    rr += dr
                    cc += dc
    return out
