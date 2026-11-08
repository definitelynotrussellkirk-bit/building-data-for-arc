"""Visible-example solution for task 167a1374f6c3."""


def _rotate_cw(pattern):
    return [list(row) for row in zip(*pattern[::-1])]


def _rotate_180(pattern):
    return [row[::-1] for row in pattern[::-1]]


def _rotate_ccw(pattern):
    return [list(row) for row in zip(*pattern)][::-1]


def _flip_left_right(pattern):
    return [row[::-1] for row in pattern]


def solve(grid):
    # The contiguous nonzero run at the upper-left is a program.  The other
    # nonzero cells form the picture to transform.
    commands = []
    for value in grid[0]:
        if value == 0:
            break
        commands.append(value)

    picture_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and r != 0
    ]
    if not picture_cells:
        return []

    r0 = min(r for r, _ in picture_cells)
    r1 = max(r for r, _ in picture_cells)
    c0 = min(c for _, c in picture_cells)
    c1 = max(c for _, c in picture_cells)
    current = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    states = [[row[:] for row in current]]
    for command in commands:
        if command == 1:
            current = _rotate_cw(current)
        elif command == 2:
            current = _rotate_180(current)
        elif command == 3:
            current = _rotate_ccw(current)
        elif command == 4:
            current = _flip_left_right(current)
        else:
            # No unseen command meaning is justified by the visible examples.
            raise ValueError(f"unsupported command color: {command}")
        states.append(current)

    out_height = max(len(state) for state in states)
    out_width = sum(len(state[0]) for state in states) + len(states) - 1
    output = [[0] * out_width for _ in range(out_height)]

    x = 0
    for index, state in enumerate(states):
        for r, row in enumerate(state):
            output[r][x : x + len(row)] = row
        x += len(state[0])
        if index + 1 < len(states):
            x += 1
    return output
