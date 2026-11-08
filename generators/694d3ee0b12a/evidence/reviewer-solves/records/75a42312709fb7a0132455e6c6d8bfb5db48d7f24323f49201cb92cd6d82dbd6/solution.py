from __future__ import annotations

from collections import Counter


def _seven_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = rr + dr, cc + dc
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == 7
                    ):
                        seen.add(point)
                        stack.append(point)
            components.append(component)
    return components


def solve(grid):
    """Fill each frame's selected row/column intersections with its local key."""
    if not grid or not grid[0]:
        return []
    output = [row[:] for row in grid]

    for component in _seven_components(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if bottom - top < 2 or right - left < 2:
            continue

        selected_rows = [
            row for row in range(top + 1, bottom)
            if grid[row][left + 1] == 2
        ]
        selected_cols = [
            col for col in range(left + 1, right)
            if grid[top + 1][col] == 3
        ]

        key_values = [
            grid[row][col]
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
            if grid[row][col] not in (0, 2, 3, 7)
        ]
        if not key_values:
            continue
        counts = Counter(key_values)
        # Counter preserves first-seen order, matching the row-major evidence
        # if two colors ever tie in frequency.
        fill_color = max(counts, key=lambda value: counts[value])

        for row in selected_rows:
            for col in selected_cols:
                output[row][col] = fill_color

    return output
