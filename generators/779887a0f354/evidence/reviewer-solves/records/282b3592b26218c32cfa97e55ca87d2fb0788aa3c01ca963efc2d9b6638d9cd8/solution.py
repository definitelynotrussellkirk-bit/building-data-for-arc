def solve(grid):
    """Mark cells seeing at least two yellow markers along unblocked rook rays."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                continue
            seen = 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = row + dr, col + dc
                while 0 <= rr < height and 0 <= cc < width:
                    if grid[rr][cc] == 5:
                        break
                    seen += grid[rr][cc] == 4
                    rr += dr
                    cc += dc
            if seen >= 2:
                out[row][col] = 2
    return out
