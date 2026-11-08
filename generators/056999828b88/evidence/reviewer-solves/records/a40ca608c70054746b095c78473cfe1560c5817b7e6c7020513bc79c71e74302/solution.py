"""Visible-example solution for the 056999828b88 review episode."""


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append((color, cells))
    return objects


def _crop(color, cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    bottom = max(row for row, _ in cells)
    right = max(col for _, col in cells)
    return {
        "color": color,
        "size": len(cells),
        "height": bottom - top + 1,
        "width": right - left + 1,
        "cells": [(row - top, col - left) for row, col in cells],
    }


def solve(grid):
    """Crop components and pack them by increasing occupied-cell count."""
    pieces = [_crop(color, cells) for color, cells in _components(grid)]
    pieces.sort(key=lambda piece: (piece["size"], piece["color"]))
    if not pieces:
        return [[0]]
    height = max(piece["height"] for piece in pieces)
    width = sum(piece["width"] for piece in pieces) + len(pieces) - 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    offset = 0
    for piece in pieces:
        for row, col in piece["cells"]:
            output[row][offset + col] = piece["color"]
        offset += piece["width"] + 1
    return output
