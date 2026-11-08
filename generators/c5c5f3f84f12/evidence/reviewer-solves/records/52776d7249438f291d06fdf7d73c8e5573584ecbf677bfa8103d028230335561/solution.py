def _normalize(cells):
    cells = list(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rotate_clockwise(cells):
    cells = _normalize(cells)
    max_row = max(r for r, _ in cells)
    return _normalize((c, max_row - r) for r, c in cells)


def solve(grid):
    """Rotate the red object by the corner encoded by the blue singleton."""
    height = len(grid)
    width = len(grid[0])
    corner_codes = {
        (0, 0): 0,
        (0, width - 1): 1,
        (height - 1, width - 1): 2,
        (height - 1, 0): 3,
    }

    blue = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    if len(blue) != 1 or blue[0] not in corner_codes:
        raise ValueError("expected one blue marker in a corner")

    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if not cells:
        raise ValueError("expected a red object")

    cells = _normalize(cells)
    for _ in range(corner_codes[blue[0]]):
        cells = _rotate_clockwise(cells)

    out_h = max(r for r, _ in cells) + 1
    out_w = max(c for _, c in cells) + 1
    output = [[0 for _ in range(out_w)] for _ in range(out_h)]
    for r, c in cells:
        output[r][c] = 8
    return output
