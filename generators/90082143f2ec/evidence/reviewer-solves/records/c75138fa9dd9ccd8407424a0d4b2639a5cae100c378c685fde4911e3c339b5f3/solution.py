"""Visible-example solution for task 90082143f2ec."""

from collections import Counter
from typing import Iterable, List, Sequence

Grid = List[List[int]]


def _mode(values: Iterable[int]) -> int:
    """Return the most frequent color, with a deterministic low-color tie-break."""
    counts = Counter(values)
    best_count = max(counts.values())
    return min(color for color, count in counts.items() if count == best_count)


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Denoise along whichever axis is more internally coherent.

    For each row and column, compute its modal color.  Score an axis by the
    number of cells already equal to the mode of their row/column.  The
    examples show that the output replaces every line on the more coherent
    axis with that line's mode.  A tie is resolved in favor of rows, matching
    the conservative branch used by the visible evidence.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    row_modes = [_mode(row) for row in grid]
    column_modes = [_mode(grid[r][c] for r in range(height)) for c in range(width)]

    row_score = sum(
        grid[r][c] == row_modes[r]
        for r in range(height)
        for c in range(width)
    )
    column_score = sum(
        grid[r][c] == column_modes[c]
        for r in range(height)
        for c in range(width)
    )

    if column_score > row_score:
        return [[column_modes[c] for c in range(width)] for _ in range(height)]
    return [[row_modes[r] for _ in range(width)] for r in range(height)]
