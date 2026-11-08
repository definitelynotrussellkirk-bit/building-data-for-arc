def solve(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    horizontal = set()
    vertical = set()
    for r in range(h):
        if grid[r][0] == 1:
            for c in range(1, w):
                if grid[r][c] == 5:
                    break
                horizontal.add((r, c))
    for c in range(w):
        if grid[0][c] == 2:
            for r in range(1, h):
                if grid[r][c] == 5:
                    break
                vertical.add((r, c))
    result = [[0] * w for _ in range(h)]
    for r, c in horizontal & vertical:
        result[r][c] = 6
    return result
