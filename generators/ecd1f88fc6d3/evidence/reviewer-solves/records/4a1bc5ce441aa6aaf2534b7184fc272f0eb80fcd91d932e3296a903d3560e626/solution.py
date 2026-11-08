"""Intentional teaching negative: numerical direction codes are ignored."""
def solve(grid):
    h, w = len(grid), len(grid[0])
    result = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if not 1 <= grid[r][c] <= 4:
                continue
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                sr, sc = r - dr, c - dc
                if 0 <= sr < h and 0 <= sc < w and grid[sr][sc] >= 5:
                    color = grid[sr][sc]
                    rr, cc = sr, sc
                    while 0 <= rr < h and 0 <= cc < w:
                        result[rr][cc] = color
                        rr += dr
                        cc += dc
    return result
