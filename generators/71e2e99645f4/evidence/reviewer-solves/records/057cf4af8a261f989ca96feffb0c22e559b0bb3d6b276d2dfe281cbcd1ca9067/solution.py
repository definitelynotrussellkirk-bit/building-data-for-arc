"""Visible-example solution for reviewer solve 71e2e99645f4."""
from __future__ import annotations

SECTION_STARTS = (0, 5, 10)
CLASS_BY_HOLES = {
    frozenset(): 2,
    frozenset({(1, 1), (1, 2), (2, 1), (2, 2)}): 8,
    frozenset({(2, 1), (2, 2), (3, 1), (3, 2)}): 4,
    frozenset({(1, 0), (1, 3), (2, 0), (2, 3)}): 3,
}


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Classify each of the three 4x4 panels by its zero-hole geometry."""
    if len(grid) != 4 or any(len(row) != 14 for row in grid):
        raise ValueError("expected a 4x14 input")

    rows: list[list[int]] = []
    for start in SECTION_STARTS:
        holes = frozenset(
            (r, c)
            for r in range(4)
            for c in range(4)
            if grid[r][start + c] == 0
        )
        try:
            color = CLASS_BY_HOLES[holes]
        except KeyError as exc:
            raise ValueError(f"unrecognized panel holes: {sorted(holes)}") from exc
        rows.append([color, color, color])
    return rows
