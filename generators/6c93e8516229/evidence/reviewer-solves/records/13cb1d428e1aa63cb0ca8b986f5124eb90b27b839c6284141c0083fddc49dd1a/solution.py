"""Visible-example solver for per-component topology recoloring."""

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in DIRS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 3
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            yield cells


def _color(cells):
    points = set(cells)
    corners = 0
    has_three_way = False
    for r, c in cells:
        neighbors = [
            (dr, dc)
            for dr, dc in DIRS
            if (r + dr, c + dc) in points
        ]
        if len(neighbors) == 3:
            has_three_way = True
        elif len(neighbors) == 2:
            first, second = neighbors
            if first[0] != second[0] and first[1] != second[1]:
                corners += 1
    if has_three_way:
        return 2
    if corners == 2:
        return 6
    return 1


def solve(grid):
    out = [row[:] for row in grid]
    for cells in _components(grid):
        color = _color(cells)
        for r, c in cells:
            out[r][c] = color
    return out
