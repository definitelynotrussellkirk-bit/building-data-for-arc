"""Visible-example solution for ARC task 71fd3c801ee1."""

from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

Grid = list[list[int]]
Cell = tuple[int, int]


def _components(grid: Grid) -> list[tuple[int, set[Cell]]]:
    """Return 4-connected non-background, same-color components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[Cell] = set()
    components: list[tuple[int, set[Cell]]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            cells: set[Cell] = {(row, col)}
            seen.add((row, col))
            pending = [(row, col)]
            while pending:
                current_row, current_col = pending.pop()
                for row_delta, col_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (current_row + row_delta, current_col + col_delta)
                    neighbor_row, neighbor_col = neighbor
                    if not (0 <= neighbor_row < height and 0 <= neighbor_col < width):
                        continue
                    if neighbor in seen or grid[neighbor_row][neighbor_col] != color:
                        continue
                    seen.add(neighbor)
                    cells.add(neighbor)
                    pending.append(neighbor)

            components.append((color, cells))

    return components


def _mask(cells: Iterable[Cell]) -> tuple[tuple[int, ...], ...]:
    cells = set(cells)
    minimum_row = min(row for row, _ in cells)
    maximum_row = max(row for row, _ in cells)
    minimum_col = min(col for _, col in cells)
    maximum_col = max(col for _, col in cells)
    return tuple(
        tuple(
            int((row, col) in cells)
            for col in range(minimum_col, maximum_col + 1)
        )
        for row in range(minimum_row, maximum_row + 1)
    )


def _hole_count(mask: tuple[tuple[int, ...], ...]) -> int:
    """Count 4-connected background regions enclosed by the component."""
    height = len(mask)
    width = len(mask[0])
    padded_height = height + 2
    padded_width = width + 2

    occupied = {
        (row + 1, col + 1)
        for row in range(height)
        for col in range(width)
        if mask[row][col]
    }
    outside: set[Cell] = {(0, 0)}
    queue: deque[Cell] = deque([(0, 0)])
    while queue:
        row, col = queue.popleft()
        for row_delta, col_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (row + row_delta, col + col_delta)
            neighbor_row, neighbor_col = neighbor
            if not (0 <= neighbor_row < padded_height and 0 <= neighbor_col < padded_width):
                continue
            if neighbor in occupied or neighbor in outside:
                continue
            outside.add(neighbor)
            queue.append(neighbor)

    unseen_background = {
        (row, col)
        for row in range(padded_height)
        for col in range(padded_width)
        if (row, col) not in occupied and (row, col) not in outside
    }
    holes = 0
    while unseen_background:
        holes += 1
        start = unseen_background.pop()
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for row_delta, col_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + row_delta, col + col_delta)
                if neighbor in unseen_background:
                    unseen_background.remove(neighbor)
                    queue.append(neighbor)
    return holes


def _reflection_axis_count(mask: tuple[tuple[int, ...], ...]) -> int:
    """Count horizontal, vertical, and (for square masks) diagonal axes."""
    height = len(mask)
    width = len(mask[0])
    horizontal = tuple(reversed(mask))
    vertical = tuple(tuple(reversed(row)) for row in mask)
    count = int(mask == horizontal) + int(mask == vertical)

    if height == width:
        main_diagonal = tuple(
            tuple(mask[col][row] for col in range(height))
            for row in range(width)
        )
        anti_diagonal = tuple(
            tuple(mask[height - 1 - col][width - 1 - row] for col in range(height))
            for row in range(width)
        )
        count += int(mask == main_diagonal) + int(mask == anti_diagonal)

    return count


def solve(grid: Grid) -> Grid:
    components = _components(grid)
    if not components:
        return [row[:] for row in grid]

    # The visible lessons contain one small distractor and four equal-area
    # candidates.  Work only with the modal component area so the distractor
    # cannot accidentally share the selected invariant.
    area_counts = Counter(len(cells) for _, cells in components)
    candidate_area = max(area_counts, key=lambda area: (area_counts[area], area))
    candidates = [component for component in components if len(component[1]) == candidate_area]

    grouped: dict[tuple[int, int], list[tuple[int, set[Cell]]]] = {}
    for component in candidates:
        component_mask = _mask(component[1])
        signature = (
            _hole_count(component_mask),
            _reflection_axis_count(component_mask),
        )
        grouped.setdefault(signature, []).append(component)

    matching_pairs = [group for group in grouped.values() if len(group) == 2]
    if len(matching_pairs) != 1:
        # Conservative fallback: do not modify an ambiguous instance.
        return [row[:] for row in grid]

    result = [row[:] for row in grid]
    for _, cells in matching_pairs[0]:
        for row, col in cells:
            result[row][col] = 8
    return result
