from copy import deepcopy


def _components_4(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def solve(grid):
    """Recolor the unique smallest 4-connected green(3) component yellow(4)."""
    out = deepcopy(grid)
    components = _components_4(grid, 3)
    if not components:
        return out
    minimum = min(len(component) for component in components)
    winners = [component for component in components if len(component) == minimum]
    if len(winners) != 1:
        return out
    for r, c in winners[0]:
        out[r][c] = 4
    return out
