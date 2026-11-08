from collections import Counter


def solve(grid):
    """Choose the symbol of the most frequent non-background color."""
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        raise ValueError("No foreground color in the input")
    winner = min(counts, key=lambda value: (-counts[value], value))
    symbols = {
        1: [[0, 5, 0], [5, 5, 5], [0, 5, 0]],
        2: [[5, 5, 5], [0, 5, 0], [0, 5, 0]],
        3: [[0, 0, 5], [0, 0, 5], [5, 5, 5]],
    }
    if winner not in symbols:
        raise ValueError("Visible examples do not teach this winning color")
    return [row[:] for row in symbols[winner]]
