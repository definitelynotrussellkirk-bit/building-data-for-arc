"""Visible-only solver for the review task.

The header encodes three independent choices:
* a unary count in columns 0..3 selects one of the four 2x2-panel objects;
* the integer in column 5 selects a geometric transform;
* the color in column 7 is used to recolor the transformed object.
"""


def _crop_nonzero(block):
    points = [
        (r, c)
        for r, row in enumerate(block)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not points:
        return []
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [row[c0 : c1 + 1] for row in block[r0 : r1 + 1]]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid, code):
    if code == 1:  # identity
        return [row[:] for row in grid]
    if code == 2:  # quarter-turn clockwise
        return _rotate_cw(grid)
    if code == 3:  # half-turn
        return [row[::-1] for row in grid[::-1]]
    if code == 4:  # quarter-turn counter-clockwise
        return _rotate_cw(_rotate_cw(_rotate_cw(grid)))
    if code == 5:  # left-right reflection
        return [row[::-1] for row in grid]
    raise ValueError(f"unsupported transform code: {code}")


def solve(grid):
    selector = sum(value == 1 for value in grid[0][:4])
    transform_code = grid[0][5]
    output_color = grid[0][7]

    if selector not in (1, 2, 3, 4):
        raise ValueError(f"invalid unary object selector: {selector}")

    row_start = 2 if selector <= 2 else 7
    col_start = 0 if selector % 2 == 1 else 5
    block = [row[col_start : col_start + 4] for row in grid[row_start : row_start + 4]]
    shape = _crop_nonzero(block)
    transformed = _transform(shape, transform_code)
    return [
        [output_color if value != 0 else 0 for value in row]
        for row in transformed
    ]
