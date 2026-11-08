"""Visible-example solution for task 95705262dbee."""

_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            min_row = min(r for r, _ in cells)
            max_row = max(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            max_col = max(c for _, c in cells)
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "top": min_row,
                    "left": min_col,
                    "bottom": max_row,
                    "right": max_col,
                }
            )

    return components


def _crop(component):
    height = component["bottom"] - component["top"] + 1
    width = component["right"] - component["left"] + 1
    piece = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in component["cells"]:
        piece[row - component["top"]][col - component["left"]] = component["color"]
    return piece


def solve(grid):
    """Sort nonzero components by cell area and pack their crops in one row."""
    if not grid or not grid[0]:
        return []

    components = _components(grid)
    components.sort(key=lambda comp: (len(comp["cells"]), comp["top"], comp["left"]))
    pieces = [_crop(component) for component in components]
    if not pieces:
        return []

    out_height = max(len(piece) for piece in pieces)
    out_width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = [[0 for _ in range(out_width)] for _ in range(out_height)]

    offset = 0
    for piece in pieces:
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                if value != 0:
                    output[row][offset + col] = value
        offset += len(piece[0]) + 1

    return output
