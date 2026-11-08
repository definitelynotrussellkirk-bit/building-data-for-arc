def solve(grid):
    """Copy each colored source to the first cyan cell on a cardinal ray."""
    h, w = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (0, 8):
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                while 0 <= rr < h and 0 <= cc < w:
                    if grid[rr][cc] == 8:
                        result[rr][cc] = color
                        break
                    rr += dr
                    cc += dc
                else:
                    continue
                break
    return result
