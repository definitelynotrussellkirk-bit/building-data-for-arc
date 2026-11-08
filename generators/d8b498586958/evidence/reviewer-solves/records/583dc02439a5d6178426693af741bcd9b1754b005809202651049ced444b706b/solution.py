"""Visible-example solver for the reviewer episode.

The input has a two-row header, a full 9 divider, panel A, another full 9
separator, and panel B. The lone color-5 corner selects a Boolean operation on
panel occupancy; selected cells are rendered as color 8.
"""
from __future__ import annotations


def solve(grid):
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")

    dividers = [index for index, row in enumerate(grid) if row == [9] * width]
    if len(dividers) != 2:
        raise ValueError(f"expected two full color-9 dividers, found {dividers}")
    first, second = dividers
    if first != 2:
        raise ValueError("expected a two-row header")

    panel_a = grid[first + 1 : second]
    panel_b = grid[second + 1 :]
    if len(panel_a) != width or len(panel_b) != width:
        raise ValueError("operand panels must be square and match input width")

    markers = [
        (row, col)
        for row in range(first)
        for col, value in enumerate(grid[row])
        if value == 5
    ]
    if len(markers) != 1:
        raise ValueError("expected one color-5 header marker")
    marker = markers[0]
    corners = {
        (0, 0): "union",
        (0, width - 1): "intersection",
        (1, 0): "xor",
        (1, width - 1): "a_minus_b",
    }
    try:
        operation = corners[marker]
    except KeyError as exc:
        raise ValueError(f"marker is not a header corner: {marker}") from exc

    occupied_a = {(r, c) for r, row in enumerate(panel_a) for c, value in enumerate(row) if value != 0}
    occupied_b = {(r, c) for r, row in enumerate(panel_b) for c, value in enumerate(row) if value != 0}

    if operation == "union":
        selected = occupied_a | occupied_b
    elif operation == "intersection":
        selected = occupied_a & occupied_b
    elif operation == "xor":
        selected = occupied_a ^ occupied_b
    else:
        selected = occupied_a - occupied_b

    return [[8 if (r, c) in selected else 0 for c in range(width)] for r in range(width)]
