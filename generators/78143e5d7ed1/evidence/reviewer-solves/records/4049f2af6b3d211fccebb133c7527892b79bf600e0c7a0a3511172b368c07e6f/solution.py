"""Visible-example solution for ARC task 78143e5d7ed1."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop components, sort them lexicographically, and bottom-pack them."""
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[tuple[tuple[int, int, int, int], list[list[int]]]] = []

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row, next_col = row + dr, col + dc
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            row0, row1 = min(rows), max(rows)
            col0, col1 = min(cols), max(cols)
            crop = [source[col0 : col1 + 1] for source in grid[row0 : row1 + 1]]
            key = (len(cells), row1 - row0 + 1, col1 - col0 + 1, color)
            objects.append((key, crop))

    objects.sort(key=lambda item: item[0])
    output_height = max(len(crop) for _, crop in objects)
    output_width = sum(len(crop[0]) for _, crop in objects) + len(objects) - 1
    output = [[0] * output_width for _ in range(output_height)]

    column = 0
    for _, crop in objects:
        top = output_height - len(crop)
        for crop_row, values in enumerate(crop):
            for crop_col, value in enumerate(values):
                output[top + crop_row][column + crop_col] = value
        column += len(crop[0]) + 1
    return output
