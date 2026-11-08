"""Visible-example solution for a4863798ed70."""
from __future__ import annotations

import math


def _red_components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }
    components = []
    while remaining:
        start = remaining.pop()
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def solve(grid):
    """Cycle each framed icon's color to the next frame clockwise."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    frames = []
    for component in _red_components(grid):
        rows = [cell[0] for cell in component]
        cols = [cell[1] for cell in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        icon_colors = {
            grid[row][col]
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
            if grid[row][col] not in (0, 1, 2)
        }
        if len(icon_colors) != 1:
            raise ValueError("each red frame must contain one icon color")
        frames.append(
            {
                "center": ((top + bottom) / 2.0, (left + right) / 2.0),
                "color": next(iter(icon_colors)),
            }
        )

    if len(frames) < 2:
        raise ValueError("expected multiple red frames")
    centroid_row = sum(frame["center"][0] for frame in frames) / len(frames)
    centroid_col = sum(frame["center"][1] for frame in frames) / len(frames)

    def clockwise_angle(frame):
        row, col = frame["center"]
        # atan2(horizontal displacement, upward displacement) measures angle
        # clockwise from 12 o'clock in screen coordinates.
        angle = math.atan2(col - centroid_col, centroid_row - row)
        return angle if angle >= 0 else angle + 2.0 * math.pi

    ordered = sorted(frames, key=clockwise_angle)
    colors = [frame["color"] for frame in ordered]
    replacement = {
        color: colors[(index + 1) % len(colors)]
        for index, color in enumerate(colors)
    }
    return [[replacement.get(value, value) for value in row] for row in grid]
