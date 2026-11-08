from __future__ import annotations

from fractions import Fraction


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
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
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(cells)})
    return sorted(
        result,
        key=lambda component: (
            Fraction(sum(col for _, col in component["cells"]), len(component["cells"])),
            Fraction(sum(row for row, _ in component["cells"]), len(component["cells"])),
        ),
    )


def _visible(grid, left, right):
    left_set, right_set = set(left), set(right)
    for left_row, left_col in left:
        for right_row, right_col in right:
            if left_row == right_row and all(
                (left_row, col) in left_set
                or (left_row, col) in right_set
                or grid[left_row][col] == 0
                for col in range(min(left_col, right_col), max(left_col, right_col) + 1)
            ):
                return True
            if left_col == right_col and all(
                (row, left_col) in left_set
                or (row, left_col) in right_set
                or grid[row][left_col] == 0
                for row in range(min(left_row, right_row), max(left_row, right_row) + 1)
            ):
                return True
    return False


def solve(grid):
    components = _components(grid)
    size = len(components)
    output = [[0 for _ in range(size)] for _ in range(size)]
    for row, left in enumerate(components):
        for col, right in enumerate(components):
            if row == col:
                output[row][col] = left["color"]
            elif _visible(grid, left["cells"], right["cells"]):
                output[row][col] = 8
    return output
