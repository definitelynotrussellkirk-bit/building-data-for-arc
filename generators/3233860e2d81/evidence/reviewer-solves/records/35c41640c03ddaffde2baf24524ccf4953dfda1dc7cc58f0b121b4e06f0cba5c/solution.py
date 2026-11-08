from collections import Counter


def solve(grid):
    """Return the three non-background colors with the largest cell counts."""
    counts = Counter(value for row in grid for value in row if value != 0)
    return [[color] for color, _ in counts.most_common(3)]
