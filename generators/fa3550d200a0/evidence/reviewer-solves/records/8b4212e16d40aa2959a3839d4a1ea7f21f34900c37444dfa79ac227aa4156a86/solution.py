"""Exposed post-repair attempt, written from the public demonstration grids."""
from collections import Counter


def solve(grid):
    counts = Counter(value for row in grid for value in row if value)
    canvas_color = counts.most_common(1)[0][0]
    canvas_cells = [(r, c) for r, row in enumerate(grid)
                    for c, value in enumerate(row) if value == canvas_color]
    r0 = min(r for r, _c in canvas_cells)
    r1 = max(r for r, _c in canvas_cells)
    c0 = min(c for _r, c in canvas_cells)
    c1 = max(c for _r, c in canvas_cells)
    result = [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]
    targets = {grid[r][c]: (r, c)
               for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
               if grid[r][c] not in (0, 2, canvas_color)}
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if value and not (r0 <= r <= r1 and c0 <= c <= c1)}
    neighbors = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        pending, component = [first], [first]
        while pending:
            r, c = pending.pop()
            for dr, dc in neighbors:
                p = r + dr, c + dc
                if p in remaining:
                    remaining.remove(p)
                    pending.append(p)
                    component.append(p)
        markers = [(r, c) for r, c in component if grid[r][c] not in (0, 2, canvas_color)]
        if len(markers) != 1:
            continue
        sr, sc = markers[0]
        target = targets.get(grid[sr][sc])
        if target is None:
            continue
        for r, c in component:
            nr, nc = target[0] + r - sr - r0, target[1] + c - sc - c0
            if 0 <= nr < len(result) and 0 <= nc < len(result[0]):
                result[nr][nc] = grid[r][c]
    return result
