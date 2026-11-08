def _shape(grid, color):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    if not cells:
        return [[False]]

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    cell_set = set(cells)
    return [
        [(r, c) in cell_set for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _crop(mask):
    cells = [
        (r, c)
        for r, row in enumerate(mask)
        for c, value in enumerate(row)
        if value
    ]
    if not cells:
        return [[0]]

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [
        [8 if mask[r][c] else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def solve(grid):
    marker = grid[0][0]
    first = _shape(grid, 1)
    second = _shape(grid, 2)

    height = max(len(first), len(second))
    width = max(len(first[0]), len(second[0]))

    def occupied(shape, r, c):
        return r < len(shape) and c < len(shape[0]) and shape[r][c]

    mask = []
    for r in range(height):
        row = []
        for c in range(width):
            a = occupied(first, r, c)
            b = occupied(second, r, c)
            if marker == 3:
                row.append(a or b)
            elif marker == 4:
                row.append(a != b)
            elif marker == 5:
                row.append(a and b)
            else:
                raise ValueError(f"unsupported operation marker: {marker}")
        mask.append(row)

    return _crop(mask)
