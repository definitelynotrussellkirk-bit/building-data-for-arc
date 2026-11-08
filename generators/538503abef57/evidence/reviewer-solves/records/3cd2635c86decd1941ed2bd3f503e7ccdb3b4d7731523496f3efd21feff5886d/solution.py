from collections import deque


def solve(grid):
    """Reflect each non-background object across its anti-diagonal."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    source = [list(row) for row in grid]
    result = [row[:] for row in source]
    seen = [[False] * width for _ in range(height)]
    components = []

    for row in range(height):
        for col in range(width):
            color = source[row][col]
            if color == 0 or seen[row][col]:
                continue

            queue = deque([(row, col)])
            seen[row][col] = True
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if seen[next_row][next_col]:
                        continue
                    if source[next_row][next_col] != color:
                        continue
                    seen[next_row][next_col] = True
                    queue.append((next_row, next_col))

            components.append((color, cells))
            for current_row, current_col in cells:
                result[current_row][current_col] = 0

    for color, cells in components:
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        box_height = bottom - top + 1
        box_width = right - left + 1

        for row, col in cells:
            local_row = row - top
            local_col = col - left
            reflected_row = box_width - 1 - local_col
            reflected_col = box_height - 1 - local_row
            result[top + reflected_row][left + reflected_col] = color

    return result
