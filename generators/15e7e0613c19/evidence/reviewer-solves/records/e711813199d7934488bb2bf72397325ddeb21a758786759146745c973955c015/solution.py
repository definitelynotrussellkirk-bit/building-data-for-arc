from collections import deque


def _components(grid):
    """Return 4-connected nonzero objects as (color, cells)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            objects.append((color, cells))

    return objects


def solve(grid):
    """Sort nonzero objects by size/shape and pack them left-to-right."""
    packed = []
    for color, cells in _components(grid):
        min_row = min(row for row, _ in cells)
        max_row = max(row for row, _ in cells)
        min_col = min(col for _, col in cells)
        max_col = max(col for _, col in cells)
        obj_height = max_row - min_row + 1
        obj_width = max_col - min_col + 1
        normalized = [(row - min_row, col - min_col) for row, col in cells]
        packed.append(
            {
                "color": color,
                "cells": normalized,
                "height": obj_height,
                "width": obj_width,
                "area": len(cells),
            }
        )

    if not packed:
        return []

    packed.sort(
        key=lambda obj: (
            obj["area"],
            obj["height"],
            obj["width"],
            obj["color"],
        )
    )

    output_height = max(obj["height"] for obj in packed)
    output_width = sum(obj["width"] for obj in packed) + len(packed) - 1
    output = [[0] * output_width for _ in range(output_height)]

    col_offset = 0
    for obj in packed:
        for row, col in obj["cells"]:
            output[row][col_offset + col] = obj["color"]
        col_offset += obj["width"] + 1

    return output
