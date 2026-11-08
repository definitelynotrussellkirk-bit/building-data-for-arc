from copy import deepcopy


def solve(grid):
    """Mark every orthogonally adjacent red/green pair.

    In each pair, erase color 2 and recolor color 3 to azure (8).  Pair
    membership is computed from the original grid so simultaneous matches do
    not depend on scan order.  All other cells are preserved.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = deepcopy(grid)
    paired_twos = set()
    paired_threes = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 3:
                continue
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                other_row = row + drow
                other_col = col + dcol
                if (
                    0 <= other_row < height
                    and 0 <= other_col < width
                    and grid[other_row][other_col] == 2
                ):
                    paired_threes.add((row, col))
                    paired_twos.add((other_row, other_col))

    for row, col in paired_twos:
        result[row][col] = 0
    for row, col in paired_threes:
        result[row][col] = 8

    return result
