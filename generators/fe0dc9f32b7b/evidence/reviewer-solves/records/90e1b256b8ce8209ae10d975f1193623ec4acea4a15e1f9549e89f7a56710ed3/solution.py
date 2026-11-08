"""Visible-example solution for the generated Nested Palette Fill episode."""
from __future__ import annotations


def _components_of_eight(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 8 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            component: set[tuple[int, int]] = set()
            while pending:
                r, c = pending.pop()
                component.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            components.append(component)
    return components


def _bounding_box(component: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    return min(rows), min(cols), max(rows), max(cols)


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill zero cells according to their depth inside valid color-8 frames."""
    source = [list(row) for row in grid]
    palette = [row[0] for row in source if row[0] not in (0, 8)]

    boxes: list[tuple[int, int, int, int]] = []
    for component in _components_of_eight(source):
        top, left, bottom, right = _bounding_box(component)
        height = bottom - top + 1
        width = right - left + 1
        perimeter_size = 2 * (height + width) - 4
        # The second visible example distinguishes a true hollow rectangular
        # frame from an overfilled rectangular-looking color-8 component.
        if height >= 3 and width >= 3 and len(component) == perimeter_size:
            boxes.append((top, left, bottom, right))

    result = [row[:] for row in source]
    for row, values in enumerate(source):
        for col, value in enumerate(values):
            if value != 0:
                continue
            depth = sum(
                top < row < bottom and left < col < right
                for top, left, bottom, right in boxes
            )
            if 1 <= depth <= len(palette):
                result[row][col] = palette[depth - 1]
    return result
