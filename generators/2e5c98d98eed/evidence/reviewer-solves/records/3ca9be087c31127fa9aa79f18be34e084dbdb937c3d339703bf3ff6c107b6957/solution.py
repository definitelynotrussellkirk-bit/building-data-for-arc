"""Infer seed-colored enclosed-region filling from visible examples only."""
from collections import deque


def solve(grid):
    out = [list(row) for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v not in (0, 8)]
    for row, col, color in seeds:
        queue = deque([(row, col)])
        seen = {(row, col)}
        while queue:
            r, c = queue.popleft()
            for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if 0 <= rr < height and 0 <= cc < width and (rr, cc) not in seen:
                    if out[rr][cc] == 0:
                        seen.add((rr, cc))
                        out[rr][cc] = color
                        queue.append((rr, cc))
    return out
