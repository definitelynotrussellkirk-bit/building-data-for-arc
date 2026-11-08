"""Visible-example solution for the exposed cf787ae40567 solve episode."""


def solve(grid):
    """Count the union of clipped orthogonal-plus neighborhoods of all nonzero cells."""
    if not grid or not grid[0]:
        return [[]]
    height = len(grid)
    width = len(grid[0])
    covered = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0:
                continue
            for drow, dcol in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = row + drow, col + dcol
                if 0 <= rr < height and 0 <= cc < width:
                    covered.add((rr, cc))
    return [[8] * len(covered)]
