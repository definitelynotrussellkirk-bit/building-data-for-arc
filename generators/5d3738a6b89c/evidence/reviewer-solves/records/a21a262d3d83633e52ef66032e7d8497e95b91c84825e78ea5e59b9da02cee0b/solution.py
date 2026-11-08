"""Visible-example solution for the post-repair episode."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    separator = next(
        row_index
        for row_index, row in enumerate(grid)
        if all(value == 9 for value in row)
    )

    divider_columns = [
        column
        for column in range(width)
        if all(grid[row][column] == 9 for row in range(separator))
    ]
    starts = [0] + [column + 1 for column in divider_columns]
    ends = divider_columns + [width]

    prototypes = {}
    for left, right in zip(starts, ends):
        if right <= left:
            continue
        key = grid[1][left + 1]
        offsets = []
        for row in range(3):
            for column in range(left, right):
                if grid[row][column] != 0:
                    offsets.append((row - 1, column - (left + 1)))
        prototypes[key] = offsets

    output = [row[:] for row in grid]
    for row in range(separator + 1, height):
        for column in range(width):
            key = grid[row][column]
            if key not in prototypes:
                continue
            for row_delta, column_delta in prototypes[key]:
                target_row = row + row_delta
                target_column = column + column_delta
                if (
                    target_row >= separator + 1
                    and 0 <= target_row < height
                    and 0 <= target_column < width
                ):
                    output[target_row][target_column] = key
    return output
