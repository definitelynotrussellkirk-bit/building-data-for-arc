from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the unique 3-by-5 window spanned by one non-background color."""
    positions: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    candidates: list[tuple[int, int, int, int]] = []
    for cells in positions.values():
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(columns), max(columns)
        if bottom - top + 1 == 3 and right - left + 1 == 5:
            candidates.append((top, bottom, left, right))

    if len(candidates) != 1:
        raise ValueError(f"expected one 3x5-spanning color, found {len(candidates)}")

    top, bottom, left, right = candidates[0]
    return [row[left : right + 1] for row in grid[top : bottom + 1]]
