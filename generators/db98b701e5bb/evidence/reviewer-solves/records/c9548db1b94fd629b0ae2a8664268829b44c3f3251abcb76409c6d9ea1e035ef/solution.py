from copy import deepcopy


def solve(grid):
    """Recolor the largest 4-connected color-2 component to color 8."""
    out = deepcopy(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    components = []

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component = []
            while stack:
                cr, cc = stack.pop()
                component.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 2
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)

    if not components:
        return out
    largest = max(components, key=len)
    for r, c in largest:
        out[r][c] = 8
    return out
