"""Visible-example solution for task 0f25172eefa4."""


def _rotate_cw(piece):
    return [list(row) for row in zip(*piece[::-1])]


def _rotate_180(piece):
    return [row[::-1] for row in piece[::-1]]


def solve(grid):
    """Render the cropped body once per nonzero code in the last row.

    Codes 2 and 5 keep the body unchanged, 3 rotates it clockwise, and
    4 rotates it 180 degrees. Pieces remain in key order, top-aligned in
    a common-height canvas, with one blank column between neighbors.
    """
    if not grid or not grid[0]:
        return []

    body_rows = grid[:-1]
    cells = [
        (r, c)
        for r, row in enumerate(body_rows)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return []

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    body = [row[c0 : c1 + 1] for row in body_rows[r0 : r1 + 1]]

    pieces = []
    for code in (value for value in grid[-1] if value != 0):
        if code in (2, 5):
            piece = [row[:] for row in body]
        elif code == 3:
            piece = _rotate_cw(body)
        elif code == 4:
            piece = _rotate_180(body)
        else:
            raise ValueError(f"unsupported visible key code: {code}")
        pieces.append(piece)

    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = [[0] * width for _ in range(height)]
    x = 0
    for index, piece in enumerate(pieces):
        for r, row in enumerate(piece):
            out[r][x : x + len(row)] = row
        x += len(piece[0])
        if index + 1 < len(pieces):
            x += 1
    return out
