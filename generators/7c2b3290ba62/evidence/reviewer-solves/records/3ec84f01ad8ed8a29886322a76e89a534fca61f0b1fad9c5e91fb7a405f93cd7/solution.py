from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Mark the two candidate panels that complete TARGET together with SOURCE."""
    if not grid or not grid[0]:
        raise ValueError("expected a non-empty grid")
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")

    separators = [
        col for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    if not separators:
        raise ValueError("missing color-9 panel separators")

    panels: list[list[list[int]]] = []
    start = 0
    for end in separators + [width]:
        panels.append([row[start:end] for row in grid])
        start = end + 1
    if len(panels) < 5:
        raise ValueError("expected SOURCE, TARGET, and at least three candidates")

    def occupied(panel: list[list[int]]) -> set[tuple[int, int]]:
        return {
            (row, col)
            for row, values in enumerate(panel)
            for col, value in enumerate(values)
            if value not in (0, 9)
        }

    source = occupied(panels[0])
    target = occupied(panels[1])
    candidates = [occupied(panel) for panel in panels[2:]]

    answer = [0] * len(candidates)
    for left in range(len(candidates)):
        for right in range(left + 1, len(candidates)):
            if source | candidates[left] | candidates[right] == target:
                answer[left] = 8
                answer[right] = 8
                return [answer]
    return [answer]
