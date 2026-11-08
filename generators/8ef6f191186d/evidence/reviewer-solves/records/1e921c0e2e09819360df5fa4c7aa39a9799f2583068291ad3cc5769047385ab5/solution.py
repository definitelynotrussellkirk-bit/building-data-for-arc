from __future__ import annotations


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    """Rotate a non-empty rectangular grid 90 degrees counterclockwise."""
    return [list(row) for row in zip(*grid)][::-1]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _flip_horizontal(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Decode the two-row palette legend and apply the coded spatial transform."""
    if len(grid) < 3 or len(grid[0]) < 1:
        raise ValueError("expected a two-row header and a pattern below it")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    operation = grid[0][0]
    mapping = {
        grid[0][col]: grid[1][col]
        for col in range(width)
        if grid[0][col] != 0 and grid[1][col] != 0
    }
    if not mapping:
        raise ValueError("no palette legend found")

    occupied = [
        (row, col)
        for row in range(2, len(grid))
        for col in range(width)
        if grid[row][col] != 0
    ]
    if not occupied:
        raise ValueError("no pattern found below the header")

    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(col for _, col in occupied)
    right = max(col for _, col in occupied)
    pattern = [row[left : right + 1] for row in grid[top : bottom + 1]]

    transforms = {
        3: _rotate_180,
        4: _rotate_ccw,
        5: _flip_horizontal,
    }
    try:
        transformed = transforms[operation](pattern)
    except KeyError as exc:
        raise ValueError(f"unknown operation code: {operation}") from exc

    return [[mapping.get(cell, cell) if cell != 0 else 0 for cell in row] for row in transformed]
