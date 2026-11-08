from collections import deque


def solve(grid):
    """Fill each 4-connected red component's bounding box with green."""
    output = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] != 2 or (start_row, start_col) in seen:
                continue

            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
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
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == 2
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))

            top = min(row for row, _ in component)
            bottom = max(row for row, _ in component)
            left = min(col for _, col in component)
            right = max(col for _, col in component)
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    output[row][col] = 3

    return output
