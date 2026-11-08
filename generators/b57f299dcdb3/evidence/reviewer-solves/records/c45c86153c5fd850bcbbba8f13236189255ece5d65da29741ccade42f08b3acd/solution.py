"""Infer the repeated colored plus from the public examples."""
from collections import Counter


def solve(grid):
    """Return the arm color of the most frequent plus centered on color 4."""
    if not grid or not grid[0]:
        raise ValueError("Expected a nonempty grid")
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")
    counts = Counter()
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 4:
                continue
            arms = (
                grid[row - 1][col], grid[row + 1][col],
                grid[row][col - 1], grid[row][col + 1],
            )
            if len(set(arms)) == 1 and arms[0] != 4:
                counts[arms[0]] += 1
    if not counts:
        raise ValueError("No four-arm plus centered on 4 found")
    maximum = max(counts.values())
    winners = [color for color, count in counts.items() if count == maximum]
    if len(winners) != 1:
        raise ValueError("No unique most frequent plus arm color")
    return [[winners[0]]]
