"""Crop the largest connected foreground object, preserving its colors."""
def solve(grid):
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            component = []
            todo = [(r, c)]
            seen.add((r, c))
            while todo:
                y, x = todo.pop()
                component.append((y, x))
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and grid[yy][xx] and (yy, xx) not in seen:
                        seen.add((yy, xx))
                        todo.append((yy, xx))
            components.append(component)
    if not components:
        return [row[:] for row in grid]
    component = max(components, key=len)
    r0 = min(r for r, c in component)
    r1 = max(r for r, c in component) + 1
    c0 = min(c for r, c in component)
    c1 = max(c for r, c in component) + 1
    return [row[c0:c1] for row in grid[r0:r1]]
