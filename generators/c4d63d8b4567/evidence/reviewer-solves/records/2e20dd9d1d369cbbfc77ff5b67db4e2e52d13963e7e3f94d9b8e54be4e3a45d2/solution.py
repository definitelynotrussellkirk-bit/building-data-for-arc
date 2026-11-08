from collections import defaultdict
from itertools import combinations


def solve(grid):
    """Connect unobstructed, same-colour markers sharing a row or column."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    positions = defaultdict(list)
    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour != 0:
                positions[colour].append((row, col))

    # Decide every segment against the original input so that one newly drawn
    # line cannot spuriously block another independent valid line.
    for colour, points in positions.items():
        for (r1, c1), (r2, c2) in combinations(points, 2):
            if r1 == r2:
                left, right = sorted((c1, c2))
                if all(grid[r1][col] == 0 for col in range(left + 1, right)):
                    for col in range(left, right + 1):
                        result[r1][col] = colour
            elif c1 == c2:
                top, bottom = sorted((r1, r2))
                if all(grid[row][c1] == 0 for row in range(top + 1, bottom)):
                    for row in range(top, bottom + 1):
                        result[row][c1] = colour

    return result
