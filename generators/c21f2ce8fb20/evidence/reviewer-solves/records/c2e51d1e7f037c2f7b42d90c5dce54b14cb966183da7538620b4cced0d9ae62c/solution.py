from collections import deque


def solve(grid):
    """Highlight the gray-separated panel containing the most red cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = [[False for _ in range(width)] for _ in range(height)]

    best = None
    for start_row in range(height):
        for start_col in range(width):
            if seen[start_row][start_col] or grid[start_row][start_col] == 5:
                continue

            queue = deque([(start_row, start_col)])
            seen[start_row][start_col] = True
            cells = []
            red_count = 0

            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                if grid[row][col] == 2:
                    red_count += 1

                for next_row, next_col in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if seen[next_row][next_col] or grid[next_row][next_col] == 5:
                        continue
                    seen[next_row][next_col] = True
                    queue.append((next_row, next_col))

            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            candidate = (
                red_count,
                min(rows),
                max(rows),
                min(cols),
                max(cols),
            )
            if best is None or candidate[0] > best[0]:
                best = candidate

    if best is None:
        return output

    _, top, bottom, left, right = best
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            output[row][col] = 8
    return output
