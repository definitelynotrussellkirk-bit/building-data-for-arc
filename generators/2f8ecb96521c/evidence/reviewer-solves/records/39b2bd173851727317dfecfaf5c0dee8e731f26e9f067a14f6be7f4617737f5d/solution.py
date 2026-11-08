from copy import deepcopy


def _components(grid, color=4):
    h = len(grid)
    w = len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def solve(grid):
    """Color each rectangle's strict interior by its relative area."""
    out = deepcopy(grid)
    components = _components(grid)
    if len(components) != 2:
        return out

    components.sort(key=len)
    for cells, interior_color in zip(components, (1, 2)):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2 = min(rows), max(rows)
        c1, c2 = min(cols), max(cols)
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                if grid[r][c] == 4:
                    out[r][c] = interior_color
    return out
