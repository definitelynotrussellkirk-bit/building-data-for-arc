from collections import deque


def solve(grid):
    """Replace each 4-connected nonzero object by its bounding-box corners."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = [[False for _ in range(width)] for _ in range(height)]

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or seen[row][col]:
                continue

            queue = deque([(row, col)])
            seen[row][col] = True
            rows = []
            cols = []

            while queue:
                current_row, current_col = queue.popleft()
                rows.append(current_row)
                cols.append(current_col)

                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if seen[next_row][next_col]:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen[next_row][next_col] = True
                    queue.append((next_row, next_col))

            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            for corner_row, corner_col in (
                (top, left),
                (top, right),
                (bottom, left),
                (bottom, right),
            ):
                output[corner_row][corner_col] = color

    return output
