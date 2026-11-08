"""Visible-example solution: nonzero color frequency selects its demonstrated glyph."""
from collections import Counter


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    counts = Counter(v for row in grid for v in row if v != 0)
    if not counts:
        raise ValueError("No foreground color")
    best = max(counts.values())
    winners = [color for color, n in counts.items() if n == best]
    if len(winners) != 1:
        raise ValueError("Visible examples do not specify a tie rule")
    # These three output shapes are copied from the visible demonstrations.
    glyphs = {
        1: ((0, 5, 0), (5, 5, 5), (0, 5, 0)),
        2: ((5, 5, 5), (0, 5, 0), (0, 5, 0)),
        3: ((0, 0, 5), (0, 0, 5), (5, 5, 5)),
    }
    if winners[0] not in glyphs:
        raise ValueError("Winning color has no visible demonstrated glyph")
    return [list(row) for row in glyphs[winners[0]]]
