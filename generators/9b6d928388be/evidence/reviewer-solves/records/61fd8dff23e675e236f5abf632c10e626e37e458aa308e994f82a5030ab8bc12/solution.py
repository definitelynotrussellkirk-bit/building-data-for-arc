"""Inferred solely from the visible challenge examples."""


def solve(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            component = {(r, c)}
            seen.add((r, c))
            stack = [(r, c)]
            while stack:
                y, x = stack.pop()
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if (0 <= yy < h and 0 <= xx < w and
                                (yy, xx) not in seen and grid[yy][xx] == color):
                            seen.add((yy, xx))
                            component.add((yy, xx))
                            stack.append((yy, xx))
            components.append((color, component))

    def bounds(points):
        return (min(y for y, x in points), max(y for y, x in points),
                min(x for y, x in points), max(x for y, x in points))

    frames = {}
    excluded = set()
    for color, points in components:
        if color != 5:
            continue
        t, b, l, r = bounds(points)
        border = {(y, x) for y in range(t, b + 1) for x in range(l, r + 1)
                  if y in (t, b) or x in (l, r)}
        if b - t >= 2 and r - l >= 2 and points == border:
            marker = (t - 1, (l + r) // 2)
            if marker[0] >= 0 and grid[marker[0]][marker[1]]:
                frames[grid[marker[0]][marker[1]]] = (t, b, l, r)
                excluded.update(points)
                excluded.add(marker)

    output = [row[:] for row in grid]
    for color, points in components:
        if points & excluded:
            continue
        t, b, l, r = bounds(points)
        empty = {(y, x) for y in range(t - 1, b + 2)
                 for x in range(l - 1, r + 2)} - points
        regions = 0
        while empty:
            regions += 1
            stack = [empty.pop()]
            while stack:
                y, x = stack.pop()
                for neighbor in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if neighbor in empty:
                        empty.remove(neighbor)
                        stack.append(neighbor)
        ft, fb, fl, fr = frames[regions]
        target_y = ft + ((fb - ft + 1) - (b - t + 1)) // 2
        target_x = fl + ((fr - fl + 1) - (r - l + 1)) // 2
        for y, x in points:
            output[y][x] = 0
        for y, x in points:
            output[target_y + y - t][target_x + x - l] = color
    return output
