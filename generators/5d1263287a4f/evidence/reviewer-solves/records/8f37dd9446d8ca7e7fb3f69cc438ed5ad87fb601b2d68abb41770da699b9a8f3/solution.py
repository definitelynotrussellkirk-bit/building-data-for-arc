from __future__ import annotations

from collections import Counter
from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Return the horizontally repeated panel.

    The examples are three equal-width panels placed side by side.  The intended
    panel is the exact panel occurring most often; in the all-equal training
    cases this naturally returns the left panel.
    """
    rows = [list(row) for row in grid]
    if not rows:
        return []

    width = len(rows[0])
    if width % 3 != 0 or any(len(row) != width for row in rows):
        raise ValueError("expected a rectangular grid made of three equal panels")

    panel_width = width // 3
    panels = [
        tuple(tuple(row[start : start + panel_width]) for row in rows)
        for start in range(0, width, panel_width)
    ]
    counts = Counter(panels)
    # max() is stable on the input order, so an all-equal/tied case selects the
    # leftmost panel without adding an arbitrary secondary rule.
    winner = max(panels, key=counts.get)
    return [list(row) for row in winner]
