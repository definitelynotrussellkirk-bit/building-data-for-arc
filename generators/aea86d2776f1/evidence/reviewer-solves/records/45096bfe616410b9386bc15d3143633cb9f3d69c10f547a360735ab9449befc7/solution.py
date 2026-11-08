"""Visible-example hypothesis for ARC task aea86d2776f1."""


def solve(grid):
    """Decode four header instructions into a two-by-two tile mosaic.

    Header codes 1--4 select the left tile and codes 5--8 select the
    right tile. Within each bank, use identity, clockwise quarter turn,
    left-right reflection, or half turn, respectively.
    """
    tiles = [
        [row[1:4] for row in grid[2:5]],
        [row[7:10] for row in grid[2:5]],
    ]
    codes = [grid[0][column] for column in (1, 3, 7, 9)]

    def transform(tile, operation):
        if operation == 0:
            return [row[:] for row in tile]
        if operation == 1:
            return [list(row) for row in zip(*tile[::-1])]
        if operation == 2:
            return [row[::-1] for row in tile]
        return [row[::-1] for row in tile[::-1]]

    quadrants = [
        transform(tiles[(code - 1) // 4], (code - 1) % 4)
        for code in codes
    ]
    return [
        quadrants[2 * block_row][row] + quadrants[2 * block_row + 1][row]
        for block_row in range(2)
        for row in range(3)
    ]
