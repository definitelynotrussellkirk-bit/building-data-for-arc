"""Visible-example solution for ARC task 40ad7195c775."""
from __future__ import annotations

from collections import Counter


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _paint_segment(
    grid: list[list[int]],
    row1: int,
    col1: int,
    row2: int,
    col2: int,
    color: int,
) -> None:
    if row1 == row2:
        for col in range(min(col1, col2), max(col1, col2) + 1):
            grid[row1][col] = color
        return
    if col1 == col2:
        for row in range(min(row1, row2), max(row1, row2) + 1):
            grid[row][col1] = color
        return
    raise ValueError("segment must be horizontal or vertical")


def _solve_horizontal(
    grid: list[list[int]],
    endpoint_color: int,
    stripe_color: int,
    marker_color: int,
) -> list[list[int]]:
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])

    endpoints = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == endpoint_color
    )
    if len(endpoints) != 2:
        raise ValueError("expected exactly two endpoint cells")
    start, goal = endpoints

    stripe_rows = sorted(
        row
        for row, values in enumerate(grid)
        if sum(value == stripe_color for value in values) > width // 2
    )
    if not stripe_rows:
        raise ValueError("expected at least one stripe")

    current_row, current_col = start[0] + 1, start[1]
    for stripe_row in stripe_rows:
        marker_cols = sorted(
            col for col, value in enumerate(grid[stripe_row]) if value == marker_color
        )
        if not marker_cols:
            raise ValueError("stripe has no marked opening")
        marker_col = marker_cols[len(marker_cols) // 2]

        _paint_segment(
            output,
            current_row,
            current_col,
            stripe_row - 1,
            current_col,
            endpoint_color,
        )
        _paint_segment(
            output,
            stripe_row - 1,
            current_col,
            stripe_row - 1,
            marker_col,
            endpoint_color,
        )
        output[stripe_row][marker_col] = endpoint_color
        current_row, current_col = stripe_row + 1, marker_col

    _paint_segment(
        output,
        current_row,
        current_col,
        goal[0] - 1,
        current_col,
        endpoint_color,
    )
    _paint_segment(
        output,
        goal[0],
        current_col,
        goal[0],
        goal[1],
        endpoint_color,
    )
    return output


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Draw the endpoint-colored staircase through the middle of each wall gap."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    counts = Counter(value for row in grid for value in row)
    background_color = max(counts, key=lambda color: (counts[color], -color))
    non_background = [color for color in counts if color != background_color]
    endpoint_candidates = [color for color in non_background if counts[color] == 2]
    if len(endpoint_candidates) != 1:
        raise ValueError("could not identify the two endpoint dots")
    endpoint_color = endpoint_candidates[0]

    remaining = [color for color in non_background if color != endpoint_color]
    if len(remaining) != 2:
        raise ValueError("expected one wall color and one marker color")
    stripe_color = max(remaining, key=lambda color: counts[color])
    marker_color = min(remaining, key=lambda color: counts[color])

    stripe_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == stripe_color
    ]
    row_peak = max(Counter(row for row, _ in stripe_cells).values())
    col_peak = max(Counter(col for _, col in stripe_cells).values())

    if row_peak > col_peak:
        return _solve_horizontal(grid, endpoint_color, stripe_color, marker_color)
    if col_peak > row_peak:
        return _transpose(
            _solve_horizontal(
                _transpose(grid), endpoint_color, stripe_color, marker_color
            )
        )
    raise ValueError("could not determine wall orientation")
