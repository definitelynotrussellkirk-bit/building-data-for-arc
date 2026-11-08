"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def _normalize(cells):
    cells = list(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _transform(cells, code):
    cells = _normalize(cells)
    h, w = _dims(cells)
    if code == 0:      # identity
        raw = cells
    elif code == 1:    # rotate clockwise
        raw = [(c, h - 1 - r) for r, c in cells]
    elif code == 2:    # rotate 180
        raw = [(h - 1 - r, w - 1 - c) for r, c in cells]
    elif code == 3:    # rotate counter-clockwise
        raw = [(w - 1 - c, r) for r, c in cells]
    elif code == 4:    # left-right reflection
        raw = [(r, w - 1 - c) for r, c in cells]
    elif code == 5:    # up-down reflection
        raw = [(h - 1 - r, c) for r, c in cells]
    elif code == 6:    # transpose
        raw = [(c, r) for r, c in cells]
    else:              # anti-transpose
        raw = [(w - 1 - c, h - 1 - r) for r, c in cells]
    return _normalize(raw)


def _panel(grid, index):
    left = 4 * index
    cells = []
    colors = []
    for r in range(3):
        for c in range(3):
            value = grid[r][left + c]
            if value != 0:
                cells.append((r, c))
                colors.append(value)
    return _normalize(cells), colors[0]


def solve(grid):
    prototypes = [_panel(grid, i) for i in range(3)]
    query_shape, query_color = _panel(grid, 3)

    matched = None
    for shape, _ in prototypes:
        if any(_transform(shape, code) == query_shape for code in range(8)):
            matched = shape
            break
    if matched is None:
        raise ValueError("query does not match any prototype under rotation/reflection")

    h, w = _dims(matched)
    output = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in matched:
        output[r][c] = query_color
    return output
