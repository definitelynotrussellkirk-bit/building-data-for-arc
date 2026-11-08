from collections import defaultdict, deque


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    points = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    out = []
    while points:
        start = points.pop()
        comp = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in points:
                    points.remove((nr, nc))
                    comp.add((nr, nc))
                    queue.append((nr, nc))
        out.append(comp)
    return out


def solve(grid):
    """Move each colored polyomino so its bounding-box corner lands on its singleton marker."""
    h, w = len(grid), len(grid[0])
    colors = sorted({cell for row in grid for cell in row if cell != 0})
    result = [[0 for _ in range(w)] for _ in range(h)]

    for color in colors:
        components = _components(grid, color)
        singleton_components = [comp for comp in components if len(comp) == 1]
        shape_components = [comp for comp in components if len(comp) > 1]

        # The visible examples pair one singleton destination marker with one
        # larger component of the same color. Leave unmatched cells unchanged
        # rather than silently discarding them.
        if len(singleton_components) != 1 or len(shape_components) != 1:
            for comp in components:
                for r, c in comp:
                    result[r][c] = color
            continue

        marker_r, marker_c = next(iter(singleton_components[0]))
        shape = shape_components[0]
        min_r = min(r for r, _ in shape)
        min_c = min(c for _, c in shape)
        for r, c in shape:
            nr = marker_r + (r - min_r)
            nc = marker_c + (c - min_c)
            if 0 <= nr < h and 0 <= nc < w:
                result[nr][nc] = color

    return result
