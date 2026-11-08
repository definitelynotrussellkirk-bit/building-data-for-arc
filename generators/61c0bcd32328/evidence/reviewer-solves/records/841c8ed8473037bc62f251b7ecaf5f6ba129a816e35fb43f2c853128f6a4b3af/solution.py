from collections import Counter, deque


def solve(grid):
    """Copy each corner-anchored monochrome object clockwise.

    Objects keep their global orientation.  A copied object is aligned to the
    corresponding two borders of the next corner and overwrites only the cells
    in its shape; the original grid is otherwise left unchanged.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return [row[:] for row in grid]

    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    output = [row[:] for row in grid]
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "min_r": min(rows),
                    "max_r": max(rows),
                    "min_c": min(cols),
                    "max_c": max(cols),
                }
            )

    # The copies are simultaneous: every source is read from the original grid.
    for component in components:
        min_r = component["min_r"]
        max_r = component["max_r"]
        min_c = component["min_c"]
        max_c = component["max_c"]

        if min_r == 0 and min_c == 0:          # top-left -> top-right
            dr, dc = 0, (width - 1) - max_c
        elif min_r == 0 and max_c == width - 1:  # top-right -> bottom-right
            dr, dc = (height - 1) - max_r, 0
        elif max_r == height - 1 and max_c == width - 1:  # bottom-right -> bottom-left
            dr, dc = 0, -min_c
        elif max_r == height - 1 and min_c == 0:  # bottom-left -> top-left
            dr, dc = -min_r, 0
        else:
            continue

        color = component["color"]
        for r, c in component["cells"]:
            output[r + dr][c + dc] = color

    return output
