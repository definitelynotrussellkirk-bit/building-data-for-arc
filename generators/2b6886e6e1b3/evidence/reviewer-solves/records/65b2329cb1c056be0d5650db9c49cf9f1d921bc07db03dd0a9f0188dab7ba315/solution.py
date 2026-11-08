def _rotate_clockwise(mask):
    return [[mask[2 - column][row] for column in range(3)] for row in range(3)]


def _rotate_180(mask):
    return [list(reversed(row)) for row in reversed(mask)]


def _flip_left_right(mask):
    return [list(reversed(row)) for row in mask]


def solve(grid):
    """Intersect the left panel with the command-transformed right panel."""
    command = grid[0][3]
    left = [[grid[row + 1][column] != 0 for column in range(3)] for row in range(3)]
    right = [[grid[row + 1][column + 4] != 0 for column in range(3)] for row in range(3)]

    if command == 1:
        transformed = right
    elif command == 2:
        transformed = _rotate_clockwise(right)
    elif command == 3:
        transformed = _flip_left_right(right)
    elif command == 4:
        transformed = _rotate_180(right)
    else:
        raise ValueError(f"unsupported command: {command}")

    return [
        [8 if left[row][column] and transformed[row][column] else 0 for column in range(3)]
        for row in range(3)
    ]
