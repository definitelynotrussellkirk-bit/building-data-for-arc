"""Visible-example solution for masked submatrix followed by command rotation."""


def _rotate_cw(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def _rotate_180(matrix):
    return [row[::-1] for row in matrix[::-1]]


def _rotate_ccw(matrix):
    return [list(row) for row in zip(*matrix)][::-1]


def solve(grid):
    command = grid[0][0]
    rows = [row for row in range(1, len(grid)) if grid[row][0] == 8]
    cols = [col for col in range(1, len(grid[0])) if grid[0][col] == 8]
    selected = [[grid[row][col] for col in cols] for row in rows]
    if command == 1:
        return selected
    if command == 2:
        return _rotate_cw(selected)
    if command == 3:
        return _rotate_180(selected)
    if command == 4:
        return _rotate_ccw(selected)
    raise ValueError(f"unknown command {command}")
