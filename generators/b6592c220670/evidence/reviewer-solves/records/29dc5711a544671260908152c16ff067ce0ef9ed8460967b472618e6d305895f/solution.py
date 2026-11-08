"""Visible-example solution for blind task b6592c220670."""


def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_horizontal(grid):
    return [row[::-1] for row in grid]


def _tight_nonzero_bbox(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def solve(grid):
    """Execute the top-row transform program on the lower object.

    Nonzero cells in the first row are commands, read left-to-right:
      1: keep the current orientation
      2: rotate it 90 degrees clockwise
      3: reflect it left-to-right
      4: rotate it 180 degrees

    After each command, emit the current tight object.  Emitted objects are
    top-aligned and separated by one zero column.
    """
    if not grid:
        return []

    commands = [value for value in grid[0] if value != 0]
    current = _tight_nonzero_bbox(grid[1:])
    if not commands or not current:
        return []

    emitted = []
    for command in commands:
        if command == 1:
            current = [row[:] for row in current]
        elif command == 2:
            current = _rotate_clockwise(current)
        elif command == 3:
            current = _flip_horizontal(current)
        elif command == 4:
            current = _rotate_180(current)
        else:
            raise ValueError(f"unsupported transform command: {command}")
        emitted.append([row[:] for row in current])

    out_h = max(len(piece) for piece in emitted)
    out_w = sum(len(piece[0]) for piece in emitted) + len(emitted) - 1
    output = [[0] * out_w for _ in range(out_h)]

    x = 0
    for piece in emitted:
        for r, row in enumerate(piece):
            output[r][x : x + len(row)] = row
        x += len(piece[0]) + 1

    return output
