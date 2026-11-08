from collections import deque


def solve(grid):
    """Keep solid monochromatic rectangles as their distinct corner cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = [[False for _ in range(width)] for _ in range(height)]

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or seen[start_row][start_col]:
                continue

            queue = deque([(start_row, start_col)])
            seen[start_row][start_col] = True
            component = []

            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                for next_row, next_col in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if seen[next_row][next_col]:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen[next_row][next_col] = True
                    queue.append((next_row, next_col))

            min_row = min(row for row, _ in component)
            max_row = max(row for row, _ in component)
            min_col = min(col for _, col in component)
            max_col = max(col for _, col in component)
            rectangle_area = (max_row - min_row + 1) * (max_col - min_col + 1)

            if len(component) != rectangle_area:
                continue

            for row, col in {
                (min_row, min_col),
                (min_row, max_col),
                (max_row, min_col),
                (max_row, max_col),
            }:
                output[row][col] = color

    return output
