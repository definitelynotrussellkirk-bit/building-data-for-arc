"""Visible-example solution for ARC task 4c4f94e7d611."""

from collections import deque


def _components(grid):
    """Return all 4-connected, same-color, non-background components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            components.append((color, cells))

    return components


def solve(grid):
    """Crop the largest object and repeat it once per singleton marker.

    Copies are laid out left-to-right with one background column between them.
    Copy 0 uses the original orientation, copy 1 a left-right reflection, and
    the orientations continue alternating.
    """
    if not grid or not grid[0]:
        return []

    components = _components(grid)
    if not components:
        return []

    template_color, template_cells = max(components, key=lambda item: len(item[1]))
    marker_count = sum(len(cells) == 1 for _, cells in components)

    min_row = min(row for row, _ in template_cells)
    max_row = max(row for row, _ in template_cells)
    min_col = min(col for _, col in template_cells)
    max_col = max(col for _, col in template_cells)

    template_set = set(template_cells)
    template = [
        [
            template_color if (row, col) in template_set else 0
            for col in range(min_col, max_col + 1)
        ]
        for row in range(min_row, max_row + 1)
    ]

    # The visible curriculum always supplies at least one singleton marker.
    # Retaining one template is a conservative fallback for a marker-free input.
    repeat_count = max(1, marker_count)
    output = [[] for _ in template]
    for index in range(repeat_count):
        copy = template if index % 2 == 0 else [list(reversed(row)) for row in template]
        if index:
            for output_row in output:
                output_row.append(0)
        for output_row, copy_row in zip(output, copy):
            output_row.extend(copy_row)

    return output
