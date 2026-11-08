from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill each nonzero color's two-marker bounding box in color order.

    Lower numeric colors claim empty cells first.  Later colors fill only cells
    that are still zero, so earlier rectangles keep precedence in overlaps and
    all original nonzero markers remain unchanged.
    """
    out = [row[:] for row in grid]
    colors = sorted({cell for row in grid for cell in row if cell != 0})

    for color in colors:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, cell in enumerate(row)
            if cell == color
        ]
        if not cells:
            continue
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if out[r][c] == 0:
                    out[r][c] = color

    return out
