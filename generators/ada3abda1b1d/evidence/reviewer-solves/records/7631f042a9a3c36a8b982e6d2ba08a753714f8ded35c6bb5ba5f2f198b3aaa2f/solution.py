from collections import Counter


def solve(grid):
    """Keep nonzero colors whose global frequency is exactly two."""
    counts = Counter(value for row in grid for value in row if value != 0)
    return [
        [value if value != 0 and counts[value] == 2 else 0 for value in row]
        for row in grid
    ]
