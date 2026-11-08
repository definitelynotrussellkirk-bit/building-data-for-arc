"""Visible-example solution for f4a7ad69b9f2."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    crops: list[list[list[int]]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            top = min(cell_row for cell_row, _ in cells)
            bottom = max(cell_row for cell_row, _ in cells)
            left = min(cell_col for _, cell_col in cells)
            right = max(cell_col for _, cell_col in cells)
            crop = [
                [grid[crop_row][crop_col] for crop_col in range(left, right + 1)]
                for crop_row in range(top, bottom + 1)
            ]
            crops.append(crop)

    crops.sort(
        key=lambda crop: (
            len(crop[0]),
            len(crop),
            tuple(value for crop_row in crop for value in crop_row),
        )
    )

    output_height = max(len(crop) for crop in crops)
    output_width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0 for _ in range(output_width)] for _ in range(output_height)]
    offset = 0
    for crop in crops:
        for crop_row, values in enumerate(crop):
            output[crop_row][offset : offset + len(values)] = values
        offset += len(crop[0]) + 1
    return output
