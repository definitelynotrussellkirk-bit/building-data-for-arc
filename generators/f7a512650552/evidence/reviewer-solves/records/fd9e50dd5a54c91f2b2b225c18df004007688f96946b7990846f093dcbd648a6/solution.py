"""Visible-example solution for f7a512650552."""
from __future__ import annotations


def _cells(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    }


def _row_close(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    out = set(cells)
    rows: dict[int, list[int]] = {}
    for r, c in cells:
        rows.setdefault(r, []).append(c)
    for r, cols in rows.items():
        out.update((r, c) for c in range(min(cols), max(cols) + 1))
    return out


def _column_close(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    out = set(cells)
    cols: dict[int, list[int]] = {}
    for r, c in cells:
        cols.setdefault(c, []).append(r)
    for c, rows in cols.items():
        out.update((r, c) for r in range(min(rows), max(rows) + 1))
    return out


def _crop_recolor(cells: set[tuple[int, int]]) -> list[list[int]]:
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [
        [8 if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Infer row- versus column-span filling from the worked example."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    separators = [
        c
        for c in range(width)
        if all(grid[r][c] == 5 for r in range(height))
    ]
    if len(separators) != 2:
        raise ValueError(f"expected two full color-5 separator columns, got {separators}")
    first, second = separators
    source = [row[:first] for row in grid]
    worked = [row[first + 1 : second] for row in grid]
    query = [row[second + 1 :] for row in grid]

    source_cells = _cells(source)
    worked_cells = _cells(worked)
    row_result = _row_close(source_cells)
    column_result = _column_close(source_cells)
    if worked_cells == row_result:
        transform = _row_close
    elif worked_cells == column_result:
        transform = _column_close
    else:
        raise ValueError("worked panel is neither row-span nor column-span closure")

    return _crop_recolor(transform(_cells(query)))
