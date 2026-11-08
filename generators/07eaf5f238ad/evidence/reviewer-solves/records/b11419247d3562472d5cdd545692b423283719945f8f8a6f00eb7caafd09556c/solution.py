"""Visible-example solution for the reviewer-authored 07eaf5f238ad episode."""
from __future__ import annotations


def _components(grid):
    if not grid:
        return []
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            found.append((color, (min(rows), min(cols), max(rows), max(cols))))
    return found


def _crop(grid, box):
    top, left, bottom, right = box
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def solve(grid):
    """Pack body components in the order indicated by nonzero header cells."""
    if not grid or not grid[0]:
        return []

    header = [color for color in grid[0] if color != 0]
    body = [list(row) for row in grid[1:]]
    components = _components(body)

    pieces = []
    for color in header:
        match = next((box for component_color, box in components if component_color == color), None)
        if match is not None:
            pieces.append(_crop(body, match))

    if not pieces:
        return [[0]]

    out_h = max(len(piece) for piece in pieces)
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = [[0 for _ in range(out_w)] for _ in range(out_h)]
    x = 0
    for piece in pieces:
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value != 0:
                    output[r][x + c] = value
        x += len(piece[0]) + 1
    return output
