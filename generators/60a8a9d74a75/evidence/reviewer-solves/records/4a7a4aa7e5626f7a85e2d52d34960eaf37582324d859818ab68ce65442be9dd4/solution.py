from collections import deque
from copy import deepcopy


def solve(grid):
    """Fill a zero component when it touches exactly one distinct non-8 colour."""
    out = deepcopy(grid)
    h = len(grid)
    w = len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)

        colors = set()
        for r, c in component:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    value = grid[nr][nc]
                    if value not in (0, 8):
                        colors.add(value)

        if len(colors) == 1:
            fill = next(iter(colors))
            for r, c in component:
                out[r][c] = fill

    return out
