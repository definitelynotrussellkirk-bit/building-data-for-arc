from __future__ import annotations

from collections import deque


BACKGROUND = 8
NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _components(grid):
    height, width = len(grid), len(grid[0])
    pending = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != BACKGROUND
    }
    components = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        cells = {start}
        pending.remove(start)
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in NEIGHBORS_8:
                neighbor = (row + dr, col + dc)
                if (
                    neighbor in pending
                    and grid[neighbor[0]][neighbor[1]] == color
                ):
                    pending.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        components.append(
            {
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            }
        )
    return components


def _nearest_to_center(component, height, width):
    center_row = (height - 1) / 2
    center_col = (width - 1) / 2
    return min(
        component["cells"],
        key=lambda cell: (
            (cell[0] - center_row) ** 2 + (cell[1] - center_col) ** 2,
            cell,
        ),
    )


def _outer_bar(component, tip):
    row1, col1, row2, col2 = component["bbox"]
    box_center_row = (row1 + row2) / 2
    box_center_col = (col1 + col2) / 2
    delta_row = tip[0] - box_center_row
    delta_col = tip[1] - box_center_col

    # The tip points inward.  Paint on the object's opposite, outward edge.
    if abs(delta_row) > abs(delta_col):
        if delta_row > 0:  # object lies above the center
            return [(row1 - 1, tip[1] + offset) for offset in (-1, 0, 1)]
        return [(row2 + 1, tip[1] + offset) for offset in (-1, 0, 1)]
    if delta_col > 0:  # object lies left of the center
        return [(tip[0] + offset, col1 - 1) for offset in (-1, 0, 1)]
    return [(tip[0] + offset, col2 + 1) for offset in (-1, 0, 1)]


def solve(grid):
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    components = _components(grid)
    for component in components:
        component["tip"] = _nearest_to_center(component, height, width)

    target = max(components, key=lambda component: len(component["cells"]))

    for component in components:
        if component is target:
            continue
        row, col = component["tip"]
        output[row][col] = BACKGROUND

    for row, col in _outer_bar(target, target["tip"]):
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = target["color"]
    return output
