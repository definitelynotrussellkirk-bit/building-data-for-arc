from collections import deque


def _components(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    found = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for row_step, col_step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + row_step
                    next_col = current_col + col_step
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    point = (next_row, next_col)
                    if point in seen or grid[next_row][next_col] != color:
                        continue
                    seen.add(point)
                    queue.append(point)
            found.append(component)
    return found


def solve(grid):
    """Double the second-smallest green object in place and recolor it cyan."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    objects = _components(grid, 3)
    if len(objects) < 2:
        return [[0 for _ in range(width)] for _ in range(height)]

    # The visible examples use distinct areas; the position key makes the
    # behavior deterministic should an equal-area input occur.
    objects.sort(key=lambda points: (
        len(points),
        min(row for row, _ in points),
        min(col for _, col in points),
    ))
    target = objects[1]
    top = min(row for row, _ in target)
    left = min(col for _, col in target)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in target:
        scaled_row = top + 2 * (row - top)
        scaled_col = left + 2 * (col - left)
        for row_offset in (0, 1):
            for col_offset in (0, 1):
                out_row = scaled_row + row_offset
                out_col = scaled_col + col_offset
                if 0 <= out_row < height and 0 <= out_col < width:
                    output[out_row][out_col] = 8
    return output
