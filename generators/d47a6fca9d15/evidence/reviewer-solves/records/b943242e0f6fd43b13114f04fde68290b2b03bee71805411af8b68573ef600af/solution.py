def solve(grid):
    """Recolor the three objects by increasing occupied area: 2, 4, 6."""
    result = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            obj = []
            while stack:
                a, b = stack.pop()
                obj.append((a, b))
                for u, v in ((a-1, b), (a+1, b), (a, b-1), (a, b+1)):
                    if (0 <= u < h and 0 <= v < w and
                            (u, v) not in seen and grid[u][v] == color):
                        seen.add((u, v))
                        stack.append((u, v))
            objects.append(obj)
    objects.sort(key=len)
    if len(objects) != 3 or len({len(obj) for obj in objects}) != 3:
        raise ValueError("Visible examples support three objects of distinct sizes")
    for color, obj in zip((2, 4, 6), objects):
        for r, c in obj:
            result[r][c] = color
    return result
