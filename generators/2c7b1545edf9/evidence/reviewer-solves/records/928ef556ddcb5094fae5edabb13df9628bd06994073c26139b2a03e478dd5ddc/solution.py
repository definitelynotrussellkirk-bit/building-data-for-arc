"""Visible-only solution for the reviewer blind episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Return the first largest 4-connected non-background color component.

    Components are discovered in row-major order, which makes ties deterministic.
    The selected component is translated to its tight bounding box; cells inside
    that box that are not part of the component remain background (0).
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    best: list[tuple[int, int]] = []
    best_color = 0

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component: list[tuple[int, int]] = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            if len(component) > len(best):
                best = component
                best_color = color

    if not best:
        return []

    min_row = min(row for row, _ in best)
    max_row = max(row for row, _ in best)
    min_col = min(col for _, col in best)
    max_col = max(col for _, col in best)
    output = [
        [0 for _ in range(max_col - min_col + 1)]
        for _ in range(max_row - min_row + 1)
    ]
    for row, col in best:
        output[row - min_row][col - min_col] = best_color
    return output
