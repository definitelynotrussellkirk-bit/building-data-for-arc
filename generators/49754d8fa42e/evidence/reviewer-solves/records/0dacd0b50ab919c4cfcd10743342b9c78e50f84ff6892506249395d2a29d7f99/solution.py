"""Infer a symbol from the most frequent nonzero input color.

The public examples identify the glyphs for colors 1, 2, and 3.
"""

from collections import Counter


_GLYPHS = {
    1: ((0, 5, 0), (5, 5, 5), (0, 5, 0)),
    2: ((5, 5, 5), (0, 5, 0), (0, 5, 0)),
    3: ((0, 0, 5), (0, 0, 5), (5, 5, 5)),
}


def solve(grid):
    """Return the public-example glyph for the dominant nonzero color."""
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        raise ValueError("The public examples do not define an all-zero input.")

    largest_count = max(counts.values())
    winners = [color for color, count in counts.items() if count == largest_count]
    if len(winners) != 1:
        raise ValueError("The public examples do not define a dominant-color tie.")

    color = winners[0]
    if color not in _GLYPHS:
        raise ValueError("No public-example glyph is available for this color.")
    return [list(row) for row in _GLYPHS[color]]
