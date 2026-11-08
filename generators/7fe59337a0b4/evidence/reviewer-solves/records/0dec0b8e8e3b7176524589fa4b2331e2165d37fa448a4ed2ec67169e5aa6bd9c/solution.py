from __future__ import annotations


def _rotate_cw(matrix: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*matrix[::-1])]


def _paste_nonzero(
    output: list[list[int]], matrix: list[list[int]], top: int, left: int
) -> None:
    for row, values in enumerate(matrix):
        for col, value in enumerate(values):
            if value:
                output[top + row][left + col] = value


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Arrange the cropped motif and its clockwise rotations around color 9."""
    height = len(grid)
    width = len(grid[0])
    marker = next(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    )
    motif_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 9)
    ]
    top = min(row for row, _ in motif_cells)
    bottom = max(row for row, _ in motif_cells)
    left = min(col for _, col in motif_cells)
    right = max(col for _, col in motif_cells)
    motif = [row[left : right + 1] for row in grid[top : bottom + 1]]

    rotations = [motif]
    for _ in range(3):
        rotations.append(_rotate_cw(rotations[-1]))

    mr, mc = marker
    north, east, south, west = rotations
    placements = (
        (north, mr - 1 - len(north), mc - len(north[0]) // 2),
        (east, mr - len(east) // 2, mc + 2),
        (south, mr + 2, mc - len(south[0]) // 2),
        (west, mr - len(west) // 2, mc - 1 - len(west[0])),
    )

    output = [[0 for _ in range(width)] for _ in range(height)]
    for matrix, out_top, out_left in placements:
        _paste_nonzero(output, matrix, out_top, out_left)
    output[mr][mc] = 9
    return output
