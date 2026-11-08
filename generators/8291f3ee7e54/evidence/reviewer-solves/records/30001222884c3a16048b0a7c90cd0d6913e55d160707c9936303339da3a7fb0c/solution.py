"""Blind solution for task 8291f3ee7e54.

Identify each non-background hollow square, infer its side length from the
largest extent still visible after overlap/clipping, and redraw the squares
concentrically from largest to smallest.
"""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0

    points_by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                points_by_color.setdefault(value, []).append((r, c))

    squares = []
    for color, points in points_by_color.items():
        rows = [r for r, _ in points]
        cols = [c for _, c in points]
        # Crossings can erase part of one edge, and a square can be clipped by
        # the canvas.  At least one axis retains the intended side in the
        # demonstrated family, so use the larger visible extent.
        side = max(max(rows) - min(rows) + 1, max(cols) - min(cols) + 1)
        squares.append((side, color))

    if not squares:
        return []

    squares.sort(reverse=True)
    outer_side = squares[0][0]
    out = [[0 for _ in range(outer_side)] for _ in range(outer_side)]

    for side, color in squares:
        offset = (outer_side - side) // 2
        last = offset + side - 1
        for i in range(offset, last + 1):
            out[offset][i] = color
            out[last][i] = color
            out[i][offset] = color
            out[i][last] = color

    return out
