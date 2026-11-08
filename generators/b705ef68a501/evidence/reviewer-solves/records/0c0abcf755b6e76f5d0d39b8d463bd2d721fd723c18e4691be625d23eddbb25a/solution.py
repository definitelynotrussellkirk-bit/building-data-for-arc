"""Visible-only solution for blind task b705ef68a501."""

from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Select the non-maroon object ranked by area, then crop it.

    The count of color-9 cells in the top row is a one-based rank. Candidate
    4-connected components exclude background (0) and the instruction color
    (9). Components are ordered by area, then by their top-left position.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    rank = sum(value == 9 for value in grid[0])
    if rank < 1:
        raise ValueError("expected at least one color-9 rank marker on row 0")

    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, int, int, int, int, list[tuple[int, int]]]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color in (0, 9) or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []

            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
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

            min_row = min(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            max_row = max(r for r, _ in cells)
            max_col = max(c for _, c in cells)
            components.append((len(cells), min_row, min_col, max_row, max_col, cells))

    components.sort(key=lambda component: component[:3])
    if rank > len(components):
        raise ValueError(f"rank {rank} exceeds {len(components)} candidate objects")

    _, min_row, min_col, max_row, max_col, cells = components[rank - 1]
    output = [[0] * (max_col - min_col + 1) for _ in range(max_row - min_row + 1)]
    for row, col in cells:
        output[row - min_row][col - min_col] = grid[row][col]
    return output
