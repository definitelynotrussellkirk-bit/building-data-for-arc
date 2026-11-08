"""Visible-example solution for the prepared 7aed1f233b46 episode."""
from __future__ import annotations


def _row_close(cells):
    by_row = {}
    for row, col in cells:
        by_row.setdefault(row, []).append(col)
    return {
        (row, col)
        for row, cols in by_row.items()
        for col in range(min(cols), max(cols) + 1)
    }


def _col_close(cells):
    by_col = {}
    for row, col in cells:
        by_col.setdefault(col, []).append(row)
    return {
        (row, col)
        for col, rows in by_col.items()
        for row in range(min(rows), max(rows) + 1)
    }


def solve(grid):
    positions = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                positions.setdefault(color, set()).add((row, col))

    winners = []
    for color, cells in positions.items():
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        rectangle = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
        }
        closed = _col_close(_row_close(cells))
        if closed == rectangle:
            winners.append((top, bottom, left, right))

    if len(winners) != 1:
        raise ValueError(f"expected one double-closure rectangle, found {len(winners)}")
    top, bottom, left, right = winners[0]
    return [[8] * (right - left + 1) for _ in range(bottom - top + 1)]
