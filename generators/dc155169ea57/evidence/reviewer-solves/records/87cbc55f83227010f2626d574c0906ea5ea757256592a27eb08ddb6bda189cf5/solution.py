"""Fresh implementation from the currently displayed examples; earlier exposure disclosed."""

def solve(grid):
    h, w = len(grid), len(grid[0])
    line = next(r for r in range(h) if grid[r] == [2] * w)
    remaining = {(r, c) for r in range(line) for c in range(w) if grid[r][c] == 1}
    objects = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = []
        while stack:
            r, c = stack.pop()
            component.append((r, c))
            for rc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if rc in remaining:
                    remaining.remove(rc)
                    stack.append(rc)
        objects.append(component)
    result = [row[:] for row in grid]
    for obj in objects:
        for r, c in obj:
            result[r][c] = 8
    line_holes = set()
    for obj in objects:
        counts = {}
        for r, c in obj:
            counts[r] = counts.get(r, 0) + 1
        supports = [r for r in counts if counts[r] >= 2]
        if supports:
            offset = line - 1 - max(supports)
        else:
            offset = h - 1 - max(counts)
            line_holes.update(c for r, c in obj)
        for r, c in obj:
            destination = r + offset
            if 0 <= destination < h:
                result[destination][c] = 1
    for c in line_holes:
        result[line][c] = 8
    return result
