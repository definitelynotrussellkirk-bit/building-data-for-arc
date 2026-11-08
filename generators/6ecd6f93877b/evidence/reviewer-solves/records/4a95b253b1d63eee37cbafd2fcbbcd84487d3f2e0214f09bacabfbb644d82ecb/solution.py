from collections import Counter


def solve(grid):
    """Count non-zero colors and emit them in ascending numeric order."""
    counts = Counter(value for row in grid for value in row if value != 0)
    output = [
        color
        for color in sorted(counts)
        for _ in range(counts[color])
    ]
    return [output or [0]]
