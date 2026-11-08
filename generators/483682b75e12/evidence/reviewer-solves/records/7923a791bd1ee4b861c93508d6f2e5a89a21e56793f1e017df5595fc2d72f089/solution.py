from collections import Counter, deque


def solve(grid):
    """Move each colored object away from the solid edge by its cell count."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [row[:] for row in grid]
    if h == 0 or w == 0:
        return out

    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]

    # The visible tasks have a solid, non-background boundary acting as the floor.
    edge = None
    if len(set(grid[-1])) == 1 and grid[-1][0] != background:
        edge = ("bottom", {(h - 1, c) for c in range(w)})
    elif len(set(grid[0])) == 1 and grid[0][0] != background:
        edge = ("top", {(0, c) for c in range(w)})
    elif len({grid[r][0] for r in range(h)}) == 1 and grid[0][0] != background:
        edge = ("left", {(r, 0) for r in range(h)})
    elif len({grid[r][-1] for r in range(h)}) == 1 and grid[0][-1] != background:
        edge = ("right", {(r, w - 1) for r in range(h)})
    else:
        return out

    side, boundary = edge
    seen = set(boundary)
    components = []

    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == background:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            component = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    if (nr, nc) in seen or (nr, nc) in boundary:
                        continue
                    if grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            components.append((color, component))

    # All objects move simultaneously, so erase every original object first.
    for _, component in components:
        for r, c in component:
            out[r][c] = background

    for color, component in components:
        distance = len(component)
        dr = dc = 0
        if side == "bottom":
            dr = -distance
        elif side == "top":
            dr = distance
        elif side == "right":
            dc = -distance
        else:  # left
            dc = distance

        for r, c in component:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in boundary:
                out[nr][nc] = color

    return out
