"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid):
    """Crop each monochromatic 4-connected object and stack by x position."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []

    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            pending = [(row, column)]
            seen.add((row, column))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        pending.append((rr, cc))

            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            crop = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
            for r, c in cells:
                crop[r - top][c - left] = color
            objects.append((left, top, crop))

    objects.sort(key=lambda item: (item[0], item[1]))
    output_width = max(len(crop[0]) for _, _, crop in objects)
    output = []
    for index, (_, _, crop) in enumerate(objects):
        if index:
            output.append([0] * output_width)
        for row in crop:
            output.append(row + [0] * (output_width - len(row)))
    return output
