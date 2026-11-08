from collections import Counter


def solve(grid):
    """Fill the grid with its most frequent non-background color.

    ARC color 0 is treated as background when any nonzero color is present.
    The output keeps the input dimensions.
    """
    if not grid or not grid[0]:
        return []

    counts = Counter(value for row in grid for value in row)
    foreground = {color: count for color, count in counts.items() if color != 0}
    candidates = foreground or dict(counts)

    # Counter iteration follows first appearance order, giving a deterministic
    # fallback if an unseen puzzle happens to contain a tie.
    fill = max(candidates, key=candidates.get)
    return [[fill for _ in row] for row in grid]
