def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def solve(grid):
    """Apply the header's cumulative motif transforms and join the states."""
    if not grid or not grid[0]:
        return []

    # The operation program is the contiguous nonzero prefix of the first row.
    operations = []
    for value in grid[0]:
        if value == 0:
            break
        operations.append(value)

    # Remove the header and crop the remaining colored motif tightly.
    body = [row[:] for row in grid]
    for col in range(len(operations)):
        body[0][col] = 0

    occupied = [
        (row_index, col_index)
        for row_index, row in enumerate(body)
        for col_index, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return []

    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(col for _, col in occupied)
    right = max(col for _, col in occupied)
    motif = [row[left : right + 1] for row in body[top : bottom + 1]]

    states = [motif]
    current = motif
    transforms = {
        1: _rotate_cw,
        2: _rotate_180,
        3: _rotate_ccw,
        4: _flip_lr,
    }
    for operation in operations:
        current = transforms[operation](current)
        states.append(current)

    output_height = max(len(state) for state in states)
    output_width = sum(len(state[0]) for state in states) + len(states) - 1
    output = [[0] * output_width for _ in range(output_height)]

    offset = 0
    for index, state in enumerate(states):
        for row_index, row in enumerate(state):
            output[row_index][offset : offset + len(row)] = row
        offset += len(state[0])
        if index + 1 < len(states):
            offset += 1

    return output
