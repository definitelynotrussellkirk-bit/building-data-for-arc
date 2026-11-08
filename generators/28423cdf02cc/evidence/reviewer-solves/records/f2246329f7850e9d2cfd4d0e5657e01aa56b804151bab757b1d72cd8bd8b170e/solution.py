def solve(grid):
    template = [row[:3] for row in grid[:3]]
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    centers = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 1]
    for r, c in centers:
        for tr in range(3):
            for tc in range(3):
                rr, cc = r + tr - 1, c + tc - 1
                if 0 <= rr < height and 0 <= cc < width and output[rr][cc] in (0, 1):
                    output[rr][cc] = template[tr][tc]
    return output
