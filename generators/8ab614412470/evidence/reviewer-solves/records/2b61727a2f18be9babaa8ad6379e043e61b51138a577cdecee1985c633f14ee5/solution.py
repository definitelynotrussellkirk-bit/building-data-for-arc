from collections import Counter


def solve(grid):
    """Erase nonzero colors that occur exactly once in the whole grid."""
    counts = Counter(value for row in grid for value in row if value != 0)
    return [
        [value if value != 0 and counts[value] > 1 else 0 for value in row]
        for row in grid
    ]
