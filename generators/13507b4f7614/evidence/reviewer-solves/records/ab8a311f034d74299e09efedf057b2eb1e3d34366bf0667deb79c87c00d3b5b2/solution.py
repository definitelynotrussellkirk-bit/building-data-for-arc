"""Visible-example solution for the reviewer solve episode."""
from collections import deque


def solve(grid):
    """Reduce each odd-height, odd-width nonzero rectangle to its center cross."""
    output = [row[:] for row in grid]
    foreground = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    remaining = set(foreground)

    while remaining:
        start = next(iter(remaining))
        component = {start}
        queue = deque([start])
        remaining.remove(start)
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)

        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        height = bottom - top + 1
        width = right - left + 1

        # The visible mixed example distinguishes the parity guard: its 4x2
        # rectangle is copied unchanged while the neighboring 5x5 becomes a cross.
        if height % 2 == 0 or width % 2 == 0:
            continue

        color = grid[top][left]
        for row, col in component:
            output[row][col] = 0
        middle_row = (top + bottom) // 2
        middle_col = (left + right) // 2
        for col in range(left, right + 1):
            output[middle_row][col] = color
        for row in range(top, bottom + 1):
            output[row][middle_col] = color

    return output
