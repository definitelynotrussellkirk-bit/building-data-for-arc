"""Visible-example-only solution for the blind ARC task."""


def _rot_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _rot_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def solve(grid):
    """Apply the encoded cumulative transforms to the isolated motif."""
    if not grid or not grid[0]:
        return []

    # The instruction is the initial nonzero run in the first row.
    codes = []
    for value in grid[0]:
        if value == 0:
            break
        codes.append(value)

    # Remove the instruction cells, then crop the remaining colored motif.
    body = [row[:] for row in grid]
    for col in range(len(codes)):
        body[0][col] = 0

    occupied = [
        (r, c)
        for r, row in enumerate(body)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return []

    r0 = min(r for r, _ in occupied)
    r1 = max(r for r, _ in occupied)
    c0 = min(c for _, c in occupied)
    c1 = max(c for _, c in occupied)
    current = [row[c0 : c1 + 1] for row in body[r0 : r1 + 1]]

    states = [[row[:] for row in current]]
    for code in codes:
        if code == 1:
            current = _rot_cw(current)
        elif code == 2:
            current = _rot_180(current)
        elif code == 3:
            current = _rot_ccw(current)
        elif code == 4:
            current = _flip_lr(current)
        else:
            raise ValueError(f"unsupported transform code: {code}")
        states.append([row[:] for row in current])

    height = max(len(state) for state in states)
    width = sum(len(state[0]) for state in states) + len(states) - 1
    output = [[0] * width for _ in range(height)]

    col = 0
    for state in states:
        for r, row in enumerate(state):
            output[r][col : col + len(row)] = row
        col += len(state[0]) + 1

    return output
