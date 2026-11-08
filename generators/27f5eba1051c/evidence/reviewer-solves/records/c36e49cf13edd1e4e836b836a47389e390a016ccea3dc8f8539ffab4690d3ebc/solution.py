"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid):
    """Select the ranked monochrome component and return its bounding crop."""
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    height = len(grid)
    width = len(grid[0])
    rank = grid[0][0]
    clean = [list(row) for row in grid]
    clean[0][0] = 0

    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if clean[row][col] != 0
    }
    components = []
    while unseen:
        start = min(unseen)
        color = clean[start[0]][start[1]]
        unseen.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if (
                    neighbor in unseen
                    and clean[neighbor[0]][neighbor[1]] == color
                ):
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        components.append(
            {
                "color": color,
                "cells": cells,
                "size": len(cells),
                "bbox": (top, bottom, left, right),
            }
        )

    ordered = sorted(
        components,
        key=lambda obj: (-obj["size"], obj["bbox"][2], obj["color"]),
    )
    selected = ordered[rank - 1]
    top, bottom, left, right = selected["bbox"]
    return [row[left : right + 1] for row in clean[top : bottom + 1]]
