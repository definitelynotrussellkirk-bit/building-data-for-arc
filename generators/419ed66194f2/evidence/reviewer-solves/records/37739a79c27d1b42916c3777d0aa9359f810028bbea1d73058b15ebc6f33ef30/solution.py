"""Solve the visible ARC task by relocating each colored template to its marker."""

from collections import deque


def _components(grid, color):
    height = len(grid)
    width = len(grid[0]) if height else 0
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def solve(grid):
    """Move each multi-cell colored object so its top-left cell meets its singleton."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        components = _components(grid, color)
        markers = [component for component in components if len(component) == 1]
        templates = [component for component in components if len(component) > 1]
        if len(markers) != 1 or len(templates) != 1:
            raise ValueError(
                f"color {color} must have one singleton marker and one template; "
                f"found sizes {[len(component) for component in components]}"
            )

        marker_row, marker_col = next(iter(markers[0]))
        template = templates[0]
        top = min(row for row, _ in template)
        left = min(col for _, col in template)

        for row, col in template:
            target_row = marker_row + row - top
            target_col = marker_col + col - left
            if not (0 <= target_row < height and 0 <= target_col < width):
                raise ValueError(f"translated color {color} leaves the grid")
            output[target_row][target_col] = color

    return output
