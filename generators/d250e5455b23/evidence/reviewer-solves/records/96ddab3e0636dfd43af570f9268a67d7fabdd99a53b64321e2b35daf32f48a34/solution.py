"""Source-closed solver inferred from the visible examples."""

from collections import deque
from typing import List

Grid = List[List[int]]


def solve(grid: Grid) -> Grid:
    """Complete each nonzero 2-cell domino into its down/right 2x2 square."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    seen: set[tuple[int, int]] = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component: list[tuple[int, int]] = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
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

            if len(component) != 2:
                # The visible task consists only of isolated dominoes. Preserve
                # any unrelated component rather than inventing extra cells.
                continue

            (r1, c1), (r2, c2) = component
            if r1 == r2 and abs(c1 - c2) == 1:
                # Horizontal domino: copy it into the row immediately below.
                target_row = r1 + 1
                if target_row < height:
                    out[target_row][c1] = color
                    out[target_row][c2] = color
            elif c1 == c2 and abs(r1 - r2) == 1:
                # Vertical domino: copy it into the column immediately right.
                target_col = c1 + 1
                if target_col < width:
                    out[r1][target_col] = color
                    out[r2][target_col] = color

    return out
