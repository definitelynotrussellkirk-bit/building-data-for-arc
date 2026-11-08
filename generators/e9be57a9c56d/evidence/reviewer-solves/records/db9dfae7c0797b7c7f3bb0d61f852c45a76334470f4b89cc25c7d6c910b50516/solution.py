from __future__ import annotations

from collections import deque
from copy import deepcopy


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
    return components


def solve(grid):
    """Replicate the colored template along the collinear marker chain."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    components = _components(grid)
    templates = [component for component in components if len(component) > 1]
    markers = [component[0] for component in components if len(component) == 1]
    if len(templates) != 1 or len(markers) < 2:
        raise ValueError("expected one multi-cell template and at least two markers")

    template = templates[0]
    template_colors = {grid[row][col] for row, col in template}
    if len(template_colors) != 1:
        raise ValueError("template must be monochrome")
    template_color = next(iter(template_colors))

    top = min(row for row, _ in template)
    left = min(col for _, col in template)
    bottom = max(row for row, _ in template)
    right = max(col for _, col in template)
    shape = [(row - top, col - left) for row, col in template]
    template_height = bottom - top + 1
    template_width = right - left + 1

    if len({row for row, _ in markers}) == 1:
        horizontal = True
        markers.sort(key=lambda cell: cell[1])
        coordinates = [col for _, col in markers]
        axis_size = template_width
    elif len({col for _, col in markers}) == 1:
        horizontal = False
        markers.sort(key=lambda cell: cell[0])
        coordinates = [row for row, _ in markers]
        axis_size = template_height
    else:
        raise ValueError("markers must be collinear")

    anchor_candidates = [
        index
        for index, (row, col) in enumerate(markers)
        if grid[row][col] == template_color
    ]
    if len(anchor_candidates) != 1:
        raise ValueError("exactly one marker must match the template color")
    anchor = anchor_candidates[0]

    origins: list[tuple[int, int] | None] = [None] * len(markers)
    origins[anchor] = (top, left)
    for index in range(anchor + 1, len(markers)):
        prev_row, prev_col = origins[index - 1]
        step = axis_size - 1 + coordinates[index] - coordinates[index - 1]
        origins[index] = (
            (prev_row, prev_col + step) if horizontal else (prev_row + step, prev_col)
        )
    for index in range(anchor - 1, -1, -1):
        next_row, next_col = origins[index + 1]
        step = axis_size - 1 + coordinates[index + 1] - coordinates[index]
        origins[index] = (
            (next_row, next_col - step) if horizontal else (next_row - step, next_col)
        )

    output = deepcopy(grid)
    height = len(grid)
    for index, ((marker_row, marker_col), origin) in enumerate(zip(markers, origins)):
        if index == anchor:
            continue
        origin_row, origin_col = origin
        color = grid[marker_row][marker_col]
        for dr, dc in shape:
            row, col = origin_row + dr, origin_col + dc
            if not (0 <= row < height and 0 <= col < width):
                raise ValueError("derived template copy leaves the grid")
            output[row][col] = color
    return output
