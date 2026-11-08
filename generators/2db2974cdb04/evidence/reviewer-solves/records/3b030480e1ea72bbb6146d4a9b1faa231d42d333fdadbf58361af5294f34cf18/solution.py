"""Visible-example solution for ARC task 2db2974cdb04."""

from collections import Counter, deque
from typing import Sequence

Grid = list[list[int]]


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Keep only zero-regions enclosed by colored cells, colored by their wall.

    Every input-colored frame is erased.  A four-connected zero component that
    reaches an outer edge is background and remains zero.  Each zero component
    fully enclosed by colored cells is painted with its surrounding color.
    """
    height = len(grid)
    if height == 0:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    output: Grid = [[0] * width for _ in range(height)]
    seen: set[tuple[int, int]] = set()
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != 0 or (start_r, start_c) in seen:
                continue

            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            component: list[tuple[int, int]] = []
            boundary_colors: Counter[int] = Counter()
            touches_edge = False

            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                if row in (0, height - 1) or col in (0, width - 1):
                    touches_edge = True

                for delta_r, delta_c in directions:
                    next_r, next_c = row + delta_r, col + delta_c
                    if not (0 <= next_r < height and 0 <= next_c < width):
                        continue
                    value = grid[next_r][next_c]
                    if value == 0:
                        position = (next_r, next_c)
                        if position not in seen:
                            seen.add(position)
                            queue.append(position)
                    else:
                        boundary_colors[value] += 1

            if not touches_edge and boundary_colors:
                fill_color = boundary_colors.most_common(1)[0][0]
                for row, col in component:
                    output[row][col] = fill_color

    return output
