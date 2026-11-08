"""Match an unrotated template shape, using only the visible lesson."""
from collections import deque


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    # The grey L separates the upper-left example from the search area.
    border_c = next(c for c, value in enumerate(grid[0]) if value == 5)
    border_r = next(r for r in range(h) if all(grid[r][c] == 5 for c in range(border_c + 1)))
    template = {(r, c) for r in range(border_r) for c in range(border_c)
                if grid[r][c] not in (0, 5)}
    def normalized(points):
        r0 = min(r for r, c in points)
        c0 = min(c for r, c in points)
        return frozenset((r-r0, c-c0) for r, c in points)
    target = normalized(template)
    seen = set()
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] in (0, 5) or (r < border_r and c < border_c):
                continue
            color = grid[r][c]
            points = {(r, c)}
            seen.add((r, c))
            queue = deque([(r, c)])
            while queue:
                rr, cc = queue.popleft()
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color
                            and not (nr < border_r and nc < border_c)):
                        seen.add((nr, nc)); points.add((nr, nc)); queue.append((nr, nc))
            if normalized(points) == target:
                for rr, cc in points:
                    out[rr][cc] = 5
    return out
