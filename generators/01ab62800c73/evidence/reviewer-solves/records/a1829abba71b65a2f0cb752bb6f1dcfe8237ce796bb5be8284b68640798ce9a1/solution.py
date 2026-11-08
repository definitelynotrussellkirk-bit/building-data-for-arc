def _crop_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return grid[::-1]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def solve(grid):
    commands = [value for value in grid[0] if value != 0]
    result = _crop_nonzero(grid[1:])
    for command in commands:
        if command == 1:
            result = _flip_lr(result)
        elif command == 2:
            result = _flip_ud(result)
        elif command == 3:
            result = _rotate_cw(result)
        elif command == 4:
            result = _rotate_180(result)
    return result
