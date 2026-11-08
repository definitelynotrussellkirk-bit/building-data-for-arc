"""Visible-example solution for ff5eb7af92e7."""
from __future__ import annotations

from collections import Counter


def solve(grid):
    """Keep the most frequent nonzero color independently in each row."""
    output = []
    for row in grid:
        counts = Counter(value for value in row if value != 0)
        if not counts:
            output.append([0] * len(row))
            continue

        # The visible examples have a unique winner.  The first-occurrence
        # tie break keeps this implementation deterministic outside that set.
        winner = max(counts, key=lambda color: (counts[color], -row.index(color)))
        output.append([value if value == winner else 0 for value in row])
    return output
