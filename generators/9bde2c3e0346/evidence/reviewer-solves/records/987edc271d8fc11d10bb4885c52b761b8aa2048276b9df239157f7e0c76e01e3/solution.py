def solve(grid):
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen and grid[nr][nc] == color:
                    unseen.remove((nr, nc))
                    cells.add((nr, nc))
                    stack.append((nr, nc))
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        for c in range(left, right + 1):
            out[top][c] = color
            out[bottom][c] = color
        for r in range(top, bottom + 1):
            out[r][left] = color
            out[r][right] = color
    return out
