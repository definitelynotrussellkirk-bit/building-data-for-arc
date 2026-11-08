def solve(grid):
    """Deliberate teaching negative: fill each same-color component's bounding box."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color, stack, cells = grid[r][c], [(r, c)], []
            seen.add((r, c))
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= ny < h and 0 <= nx < w and (ny, nx) not in seen and grid[ny][nx] == color:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            r1 = min(y for y, _ in cells); r2 = max(y for y, _ in cells)
            c1 = min(x for _, x in cells); c2 = max(x for _, x in cells)
            for y in range(r1, r2 + 1):
                for x in range(c1, c2 + 1):
                    out[y][x] = color
    return out
