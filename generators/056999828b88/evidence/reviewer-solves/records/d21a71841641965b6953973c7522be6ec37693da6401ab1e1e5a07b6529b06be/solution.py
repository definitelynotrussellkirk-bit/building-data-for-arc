"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def _objects(grid: list[list[int]]) -> list[dict[str, object]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[dict[str, object]] = []

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
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            min_row = min(row for row, _ in cells)
            max_row = max(row for row, _ in cells)
            min_col = min(col for _, col in cells)
            max_col = max(col for _, col in cells)
            normalized = [(row - min_row, col - min_col) for row, col in cells]
            objects.append(
                {
                    "color": color,
                    "cells": normalized,
                    "size": len(cells),
                    "height": max_row - min_row + 1,
                    "width": max_col - min_col + 1,
                }
            )
    return objects


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop each colored object, sort by cell count, and pack with one blank column."""
    objects = _objects(grid)
    if not objects:
        return [[0]]

    objects.sort(key=lambda obj: (int(obj["size"]), int(obj["color"])))
    out_height = max(int(obj["height"]) for obj in objects)
    out_width = sum(int(obj["width"]) for obj in objects) + len(objects) - 1
    output = [[0 for _ in range(out_width)] for _ in range(out_height)]

    offset = 0
    for obj in objects:
        color = int(obj["color"])
        for row, col in obj["cells"]:  # type: ignore[union-attr]
            output[row][offset + col] = color
        offset += int(obj["width"]) + 1
    return output
