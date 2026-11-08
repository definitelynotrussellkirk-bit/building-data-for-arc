from collections import deque


def _five_components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 5 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            yield component


def solve(grid):
    """Project each outside orange marker through its gray rectangle."""
    output = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for component in _five_components(grid):
        top = min(row for row, _ in component)
        bottom = max(row for row, _ in component)
        left = min(col for _, col in component)
        right = max(col for _, col in component)

        if bottom - top < 2 or right - left < 2:
            continue

        # A marker immediately outside the top or bottom side paints its
        # aligned interior column. A marker outside either vertical side
        # paints its aligned interior row.
        for col in range(left + 1, right):
            if top > 0 and grid[top - 1][col] == 7:
                for row in range(top + 1, bottom):
                    if output[row][col] == 0:
                        output[row][col] = 3
            if bottom + 1 < height and grid[bottom + 1][col] == 7:
                for row in range(top + 1, bottom):
                    if output[row][col] == 0:
                        output[row][col] = 3

        for row in range(top + 1, bottom):
            if left > 0 and grid[row][left - 1] == 7:
                for col in range(left + 1, right):
                    if output[row][col] == 0:
                        output[row][col] = 3
            if right + 1 < width and grid[row][right + 1] == 7:
                for col in range(left + 1, right):
                    if output[row][col] == 0:
                        output[row][col] = 3

    return output
