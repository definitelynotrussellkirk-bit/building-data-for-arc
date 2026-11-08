"""Blind solution inferred only from the visible challenge examples."""


def solve(grid):
    """Recolor each gray (5) cell by its local orthogonal geometry.

    Fully surrounded cells become red (2), terminal/corner cells become blue
    (1), and straight/edge/junction cells become yellow (4). Other colors are
    preserved.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5:
                continue

            same_directions = []
            for drow, dcol in directions:
                other_row = row + drow
                other_col = col + dcol
                if (
                    0 <= other_row < height
                    and 0 <= other_col < width
                    and grid[other_row][other_col] == 5
                ):
                    same_directions.append((drow, dcol))

            degree = len(same_directions)
            if degree == 4:
                output[row][col] = 2
            elif degree <= 1:
                output[row][col] = 1
            elif degree == 2:
                first, second = same_directions
                opposite = first[0] == -second[0] and first[1] == -second[1]
                output[row][col] = 4 if opposite else 1
            else:
                output[row][col] = 4

    return output
