"""Recolor isolated horizontal gray dominoes from visible demonstrations."""
def solve(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component = []
            while stack:
                a, b = stack.pop()
                component.append((a, b))
                for da, db in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    x, y = a + da, b + db
                    if 0 <= x < h and 0 <= y < w and grid[x][y] == 5 and (x, y) not in seen:
                        seen.add((x, y))
                        stack.append((x, y))
            if len(component) == 2 and component[0][0] == component[1][0]:
                for a, b in component:
                    out[a][b] = 8
    return out
