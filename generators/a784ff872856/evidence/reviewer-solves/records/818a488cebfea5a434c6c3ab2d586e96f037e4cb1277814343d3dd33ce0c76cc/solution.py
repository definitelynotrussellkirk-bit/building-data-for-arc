"""Visible-example solution for the post-repair episode."""


def _objects(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            cells = [(row, col)]
            seen.add((row, col))
            for current_row, current_col in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + dr
                    next_col = current_col + dc
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        cells.append((next_row, next_col))

            min_row = min(r for r, _ in cells)
            max_row = max(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            max_col = max(c for _, c in cells)
            normalized = [(r - min_row, c - min_col) for r, c in cells]
            objects.append(
                {
                    "color": color,
                    "cells": normalized,
                    "height": max_row - min_row + 1,
                    "width": max_col - min_col + 1,
                }
            )
    return objects


def solve(grid):
    objects = _objects(grid)
    objects.sort(key=lambda obj: (-obj["width"], -obj["height"], obj["color"]))

    output_height = sum(obj["height"] for obj in objects) + max(0, len(objects) - 1)
    output_width = max((obj["width"] for obj in objects), default=0)
    output = [[0 for _ in range(output_width)] for _ in range(output_height)]

    top = 0
    for obj in objects:
        for row, col in obj["cells"]:
            output[top + row][col] = obj["color"]
        top += obj["height"] + 1
    return output
