"""Visible-example solution for the prepared ARC episode."""

_KNIGHT_OFFSETS = (
    (-2, -1), (-2, 1),
    (-1, -2), (-1, 2),
    (1, -2), (1, 2),
    (2, -1), (2, 1),
)


def solve(grid):
    """Paint every nonzero seed and its in-bounds chess-knight halo.

    Seeds are visited in row-major order, so a later seed's color wins wherever
    two halos overlap.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            output[row][col] = color
            for drow, dcol in _KNIGHT_OFFSETS:
                rr, cc = row + drow, col + dcol
                if 0 <= rr < height and 0 <= cc < width:
                    output[rr][cc] = color
    return output
