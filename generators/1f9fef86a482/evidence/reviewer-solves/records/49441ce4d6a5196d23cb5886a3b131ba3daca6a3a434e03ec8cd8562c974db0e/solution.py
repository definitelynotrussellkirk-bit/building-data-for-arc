"""Visible-example solution for the reviewer-authored episode."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    target_degree = sum(value == 1 for value in grid[0])

    seen = set()
    components = []
    # Row 0 is the legend.  Treat every non-zero same-colour 4-component below
    # it as one graph vertex.
    for row in range(1, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(set(cells))

    neighbors = [set() for _ in components]
    for first in range(len(components)):
        for second in range(first + 1, len(components)):
            if any(
                (row + dr, col + dc) in components[second]
                for row, col in components[first]
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                neighbors[first].add(second)
                neighbors[second].add(first)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for cells, adjacent in zip(components, neighbors):
        if len(adjacent) == target_degree:
            for row, col in cells:
                output[row][col] = 8
    return output
