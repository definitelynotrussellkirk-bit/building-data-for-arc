from __future__ import annotations

from collections import Counter
from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Render one left-aligned area bar for each nonzero color, sorted by color."""
    counts = Counter(cell for row in grid for cell in row if cell != 0)
    if not counts:
        return []
    width = max(counts.values())
    return [
        [color] * counts[color] + [0] * (width - counts[color])
        for color in sorted(counts)
    ]
