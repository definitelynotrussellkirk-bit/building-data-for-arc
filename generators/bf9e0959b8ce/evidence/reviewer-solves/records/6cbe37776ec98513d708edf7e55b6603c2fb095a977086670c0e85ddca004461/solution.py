from __future__ import annotations

from collections import Counter


def _mode(values):
    return Counter(values).most_common(1)[0][0]


def solve(grid):
    h, w = len(grid), len(grid[0])

    # Horizontal separator: sparse source above, aligned key immediately below.
    for sep in range(1, h - 1):
        if not all(grid[sep][c] == grid[sep][0] for c in range(w)):
            continue
        source_values = [grid[r][c] for r in range(sep) for c in range(w)]
        bg = _mode(source_values)
        if grid[sep][0] == bg:
            continue
        dots = [
            (r, c, grid[r][c])
            for r in range(sep)
            for c in range(w)
            if grid[r][c] != bg
        ]
        if not dots:
            continue
        out = [row[:] for row in grid]
        key_row = sep + 1
        for r, c, color in dots:
            out[r][c] = bg
            destination = sep - 1 if color == grid[key_row][c] else 0
            out[destination][c] = color
        return out

    # Vertical separator: aligned key immediately left, sparse source right.
    for sep in range(1, w - 1):
        if not all(grid[r][sep] == grid[0][sep] for r in range(h)):
            continue
        source_values = [grid[r][c] for r in range(h) for c in range(sep + 1, w)]
        bg = _mode(source_values)
        if grid[0][sep] == bg:
            continue
        dots = [
            (r, c, grid[r][c])
            for r in range(h)
            for c in range(sep + 1, w)
            if grid[r][c] != bg
        ]
        if not dots:
            continue
        out = [row[:] for row in grid]
        key_col = sep - 1
        for r, c, color in dots:
            out[r][c] = bg
            destination = sep + 1 if color == grid[r][key_col] else w - 1
            out[r][destination] = color
        return out

    return [row[:] for row in grid]
