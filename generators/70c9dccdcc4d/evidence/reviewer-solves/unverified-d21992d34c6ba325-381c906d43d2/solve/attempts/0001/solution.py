"""Visible-example solution for the exposed post-repair episode."""
from __future__ import annotations

from copy import deepcopy

CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _find_frame(grid, origin_color, x_color, y_color):
    height, width = len(grid), len(grid[0])
    candidates = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != origin_color:
                continue
            for x_axis in CARDINALS:
                for y_axis in CARDINALS:
                    if x_axis[0] * y_axis[0] + x_axis[1] * y_axis[1] != 0:
                        continue
                    xr, xc = row + x_axis[0], col + x_axis[1]
                    yr, yc = row + y_axis[0], col + y_axis[1]
                    if (
                        0 <= xr < height
                        and 0 <= xc < width
                        and 0 <= yr < height
                        and 0 <= yc < width
                        and grid[xr][xc] == x_color
                        and grid[yr][yc] == y_color
                    ):
                        candidates.append(((row, col), x_axis, y_axis))
    if not candidates:
        raise ValueError(f"frame {origin_color}/{x_color}/{y_color} not found")
    return min(candidates)


def _local(frame, row, col):
    (origin_row, origin_col), x_axis, y_axis = frame
    dr, dc = row - origin_row, col - origin_col
    return (
        dr * x_axis[0] + dc * x_axis[1],
        dr * y_axis[0] + dc * y_axis[1],
    )


def _global(frame, u, v):
    (origin_row, origin_col), x_axis, y_axis = frame
    return (
        origin_row + u * x_axis[0] + v * y_axis[0],
        origin_col + u * x_axis[1] + v * y_axis[1],
    )


def solve(grid):
    source = _find_frame(grid, 2, 3, 4)
    target = _find_frame(grid, 5, 6, 7)
    height, width = len(grid), len(grid[0])
    output = deepcopy(grid)

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 8:
                continue
            u, v = _local(source, row, col)
            if max(abs(u), abs(v)) > 3:
                continue
            target_row, target_col = _global(target, v, u)
            if 0 <= target_row < height and 0 <= target_col < width:
                output[target_row][target_col] = 8
    return output
