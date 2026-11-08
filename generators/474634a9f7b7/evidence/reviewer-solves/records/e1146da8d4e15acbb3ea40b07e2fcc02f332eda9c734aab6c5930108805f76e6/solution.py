from collections import deque


def _components(grid, background=8):
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    }
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        cells = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    neighbor = row + dr, col + dc
                    if (
                        neighbor in unseen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        unseen.remove(neighbor)
                        cells.add(neighbor)
                        queue.append(neighbor)
        result.append({"color": color, "cells": cells})
    return result


def _tip(component, height, width):
    center_row = (height - 1) / 2
    center_col = (width - 1) / 2
    return min(
        component["cells"],
        key=lambda cell: (
            (cell[0] - center_row) ** 2 + (cell[1] - center_col) ** 2,
            cell,
        ),
    )


def solve(grid):
    """Keep the largest object's inward tip, erase the other three, add its outer bar."""
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    components = _components(grid)
    for component in components:
        component["tip"] = _tip(component, height, width)
        rows = [row for row, _ in component["cells"]]
        cols = [col for _, col in component["cells"]]
        component["bbox"] = min(rows), min(cols), max(rows), max(cols)

    target = max(components, key=lambda component: len(component["cells"]))
    for component in components:
        if component is not target:
            row, col = component["tip"]
            output[row][col] = 8

    row1, col1, row2, col2 = target["bbox"]
    tip_row, tip_col = target["tip"]
    body_row = (row1 + row2) / 2
    body_col = (col1 + col2) / 2
    dr = tip_row - body_row
    dc = tip_col - body_col

    if abs(dr) > abs(dc):
        bar_row = row1 - 1 if dr > 0 else row2 + 1
        bar = [(bar_row, tip_col + offset) for offset in (-1, 0, 1)]
    else:
        bar_col = col1 - 1 if dc > 0 else col2 + 1
        bar = [(tip_row + offset, bar_col) for offset in (-1, 0, 1)]

    for row, col in bar:
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = target["color"]
    return output
