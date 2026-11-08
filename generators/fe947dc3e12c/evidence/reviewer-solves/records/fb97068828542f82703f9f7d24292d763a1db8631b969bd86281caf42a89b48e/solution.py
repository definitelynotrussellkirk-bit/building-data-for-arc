"""Visible-example solution for the exposed post-repair episode."""
from __future__ import annotations


def solve(grid):
    """Rank the three nonzero 4-connected objects by cell count and recolor them."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] != 0
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(cells)

    ordered = sorted(components, key=lambda cells: (-len(cells), min(cells)))
    if len(ordered) != 3 or len({len(cells) for cells in ordered}) != 3:
        raise ValueError("expected three nonzero 4-connected objects with distinct sizes")

    answer = [row[:] for row in grid]
    for color, cells in zip((1, 4, 2), ordered):
        for row, col in cells:
            answer[row][col] = color
    return answer
