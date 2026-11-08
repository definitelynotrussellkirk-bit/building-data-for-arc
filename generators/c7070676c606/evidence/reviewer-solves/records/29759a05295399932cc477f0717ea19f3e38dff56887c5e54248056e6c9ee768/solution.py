"""Visible-only solution for task c7070676c606.

Blue cells mark guide columns.  Among the 4-connected gray objects, recolor the
object that occupies the greatest number of those guide columns.
"""


def _components(grid, color):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue

            component = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(component)

    return result


def solve(grid):
    output = [row[:] for row in grid]
    guide_columns = {
        col
        for row in grid
        for col, value in enumerate(row)
        if value == 1
    }
    gray_objects = _components(grid, 3)
    if not gray_objects:
        return output

    # Count each guide column at most once, even when blue markers appear at
    # both ends of the same column.
    target = max(
        gray_objects,
        key=lambda component: len({c for _, c in component} & guide_columns),
    )
    for row, col in target:
        output[row][col] = 2
    return output
