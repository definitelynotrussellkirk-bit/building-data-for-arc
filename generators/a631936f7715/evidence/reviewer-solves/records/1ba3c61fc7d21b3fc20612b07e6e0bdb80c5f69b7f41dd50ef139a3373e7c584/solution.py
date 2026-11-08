"""Visible-example-only solution for task a631936f7715."""

from collections import deque


def solve(grid):
    """Transfer each non-background marker color onto an adjacent gray object.

    Gray (6) cells form 4-connected objects on background color 7.  A colored
    marker orthogonally touching an object paints that entire object; marker
    cells themselves are erased to the background.  Unmarked gray objects stay
    gray, and isolated markers simply disappear.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    out = [[7 if value not in (6, 7) else value for value in row] for row in grid]
    seen = [[False] * width for _ in range(height)]
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] != 6 or seen[start_row][start_col]:
                continue

            component = []
            marker_colors = []
            queue = deque([(start_row, start_col)])
            seen[start_row][start_col] = True

            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                for delta_row, delta_col in directions:
                    next_row = row + delta_row
                    next_col = col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    value = grid[next_row][next_col]
                    if value == 6 and not seen[next_row][next_col]:
                        seen[next_row][next_col] = True
                        queue.append((next_row, next_col))
                    elif value not in (6, 7):
                        marker_colors.append(value)

            unique_markers = set(marker_colors)
            if len(unique_markers) == 1:
                paint = next(iter(unique_markers))
                for row, col in component:
                    out[row][col] = paint

    return out
