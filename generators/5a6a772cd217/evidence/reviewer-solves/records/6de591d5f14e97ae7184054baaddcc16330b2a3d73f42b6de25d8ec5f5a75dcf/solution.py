from __future__ import annotations

from collections import deque


def _five_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 5
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        unseen_component = {start}
        queue = deque([start])
        while queue:
            row, column = queue.popleft()
            for neighbor in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    unseen_component.add(neighbor)
                    queue.append(neighbor)
        components.append(unseen_component)
    return components


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extract color-5 frame interiors and gallery-pack them in row-major order."""
    if not grid or not grid[0]:
        return []

    boxes: list[tuple[int, int, int, int]] = []
    for component in _five_components(grid):
        rows = [row for row, _ in component]
        columns = [column for _, column in component]
        boxes.append((min(rows), min(columns), max(rows), max(columns)))
    boxes.sort(key=lambda box: (box[0], box[1]))

    interiors = [
        [
            list(grid[row][left + 1 : right])
            for row in range(top + 1, bottom)
        ]
        for top, left, bottom, right in boxes
    ]
    if not interiors:
        return []

    target_height = max(len(interior) for interior in interiors)
    panels: list[list[list[int]]] = []
    for index, interior in enumerate(interiors):
        source_height = len(interior)
        source_width = len(interior[0])
        narrow = source_width < 3
        target_width = source_width + (1 if narrow else 0)
        left_pad = 1 if narrow and index > 0 else 0
        panel = [[0 for _ in range(target_width)] for _ in range(target_height)]
        for row in range(source_height):
            for column in range(source_width):
                panel[row][column + left_pad] = interior[row][column]
        panels.append(panel)

    return [
        [value for panel in panels for value in panel[row]]
        for row in range(target_height)
    ]
