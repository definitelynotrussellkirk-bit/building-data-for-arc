def _rotate_clockwise(cells, height, width):
    """Rotate normalized (row, col) cells 90 degrees clockwise."""
    return {(c, height - 1 - r) for r, c in cells}, width, height


def solve(grid):
    """Move the 1-object to the orange marker, rotate by the code color, recolor 8."""
    rows, cols = len(grid), len(grid[0])

    ones = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if not ones:
        return [[0] * cols for _ in range(rows)]

    anchor = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 7
    )
    code = next(
        value
        for row in grid
        for value in row
        if value not in (0, 1, 7)
    )

    min_r = min(r for r, _ in ones)
    max_r = max(r for r, _ in ones)
    min_c = min(c for _, c in ones)
    max_c = max(c for _, c in ones)
    cells = {(r - min_r, c - min_c) for r, c in ones}
    height = max_r - min_r + 1
    width = max_c - min_c + 1

    quarter_turns = {2: 0, 3: 1, 4: 2, 6: 3}[code]
    for _ in range(quarter_turns):
        cells, height, width = _rotate_clockwise(cells, height, width)

    out = [[0] * cols for _ in range(rows)]
    anchor_r, anchor_c = anchor
    for r, c in cells:
        rr, cc = anchor_r + r, anchor_c + c
        if 0 <= rr < rows and 0 <= cc < cols:
            out[rr][cc] = 8
    return out
