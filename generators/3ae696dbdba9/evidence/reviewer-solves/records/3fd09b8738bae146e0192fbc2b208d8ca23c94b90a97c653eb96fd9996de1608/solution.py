"""Visible-only ARC solver for task 3ae696dbdba9.

For each 4-connected non-background object, fill background cells bracketed
by that object's colour in a row or a column.  Brackets are measured in the
original object, so separate same-colour objects are never joined and newly
filled cells cannot trigger a second wave.
"""

from collections import deque


def _components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    for r in range(height):
        for c in range(width):
            colour = grid[r][c]
            if colour == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield colour, cells


def solve(grid):
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    source = [list(row) for row in grid]
    result = [row[:] for row in source]

    for colour, cells in _components(source):
        by_row = {}
        by_col = {}
        for r, c in cells:
            by_row.setdefault(r, []).append(c)
            by_col.setdefault(c, []).append(r)

        for r, cols in by_row.items():
            if len(cols) >= 2:
                for c in range(min(cols) + 1, max(cols)):
                    if source[r][c] == 0:
                        result[r][c] = colour

        for c, rows in by_col.items():
            if len(rows) >= 2:
                for r in range(min(rows) + 1, max(rows)):
                    if source[r][c] == 0:
                        result[r][c] = colour

    return result
