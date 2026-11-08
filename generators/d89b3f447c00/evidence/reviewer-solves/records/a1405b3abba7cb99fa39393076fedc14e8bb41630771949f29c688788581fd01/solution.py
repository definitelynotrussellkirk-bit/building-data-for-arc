from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Complete each same-colored axis-aligned rectangle missing one corner.

    Nonzero cells of a color may include an unrelated distractor.  Candidate
    rectangles are therefore discovered from the original grid, and every
    rectangle having exactly three colored corners and one empty corner is
    completed without cascading from newly added cells.
    """
    result = [list(row) for row in grid]
    positions: dict[int, set[tuple[int, int]]] = defaultdict(set)

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].add((row_index, column_index))

    additions: set[tuple[int, int, int]] = set()
    for color, cells in positions.items():
        if len(cells) < 3:
            continue
        rows = sorted({row for row, _ in cells})
        columns = sorted({column for _, column in cells})

        for top, bottom in combinations(rows, 2):
            for left, right in combinations(columns, 2):
                corners = {
                    (top, left),
                    (top, right),
                    (bottom, left),
                    (bottom, right),
                }
                present = corners & cells
                if len(present) != 3:
                    continue
                missing = next(iter(corners - present))
                row, column = missing
                if grid[row][column] == 0:
                    additions.add((row, column, color))

    for row, column, color in additions:
        result[row][column] = color
    return result
