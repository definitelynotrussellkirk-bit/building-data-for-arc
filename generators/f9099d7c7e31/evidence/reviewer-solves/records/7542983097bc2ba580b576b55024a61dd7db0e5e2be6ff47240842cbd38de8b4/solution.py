"""Visible-example solver: widest same-color component; break ties by cell count.

Return the original-input crop, preserving foreign colors and zeros.
"""
from collections import deque


def _objects(grid):
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0] or any(len(row) != len(grid[0]) for row in grid)):
        raise ValueError('Expected a nonempty rectangular list of lists')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('Grid colors must be integers in 0..9')
    h, w = len(grid), len(grid[0])
    visited = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in visited:
                continue
            color = grid[r][c]
            pending = deque([(r, c)])
            visited.add((r, c))
            cells = []
            while pending:
                x, y = pending.popleft()
                cells.append((x, y))
                for a, b in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                    if (0 <= a < h and 0 <= b < w and (a, b) not in visited
                            and grid[a][b] == color):
                        visited.add((a, b))
                        pending.append((a, b))
            lo_r = min(x for x, _ in cells)
            hi_r = max(x for x, _ in cells)
            lo_c = min(y for _, y in cells)
            hi_c = max(y for _, y in cells)
            out.append({'cells': cells, 'box': (lo_r, hi_r, lo_c, hi_c),
                        'width': hi_c-lo_c+1, 'height': hi_r-lo_r+1,
                        'color': color})
    return out


def solve(grid):
    objects = _objects(grid)
    if not objects:
        raise ValueError('No nonzero connected object')
    chosen = max(objects, key=lambda obj: (obj['width'], len(obj['cells'])))
    r0, r1, c0, c1 = chosen['box']
    return [row[c0:c1+1] for row in grid[r0:r1+1]]
