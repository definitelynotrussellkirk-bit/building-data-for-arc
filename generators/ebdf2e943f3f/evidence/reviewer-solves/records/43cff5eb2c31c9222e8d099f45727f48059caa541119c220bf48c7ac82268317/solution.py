from collections import deque


def solve(grid):
    """Complete each non-background 4-connected component's bounding rectangle."""
    out = [row[:] for row in grid]
    if not grid:
        return out

    height = len(grid)
    width = len(grid[0])
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []

            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            min_row = min(point[0] for point in component)
            max_row = max(point[0] for point in component)
            min_col = min(point[1] for point in component)
            max_col = max(point[1] for point in component)
            for fill_row in range(min_row, max_row + 1):
                for fill_col in range(min_col, max_col + 1):
                    if out[fill_row][fill_col] == 0:
                        out[fill_row][fill_col] = color

    return out
