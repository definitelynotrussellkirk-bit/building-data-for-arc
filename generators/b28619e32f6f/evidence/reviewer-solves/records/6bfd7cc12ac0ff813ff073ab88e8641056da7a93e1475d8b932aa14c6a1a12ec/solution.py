from collections import deque


def solve(grid):
    """Color enclosed zero regions from smallest to largest."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    seen = [[False] * width for _ in range(height)]
    enclosed = []

    for start_row in range(height):
        for start_col in range(width):
            if seen[start_row][start_col] or grid[start_row][start_col] != 0:
                continue

            queue = deque([(start_row, start_col)])
            seen[start_row][start_col] = True
            component = []
            touches_border = False

            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                if row in (0, height - 1) or col in (0, width - 1):
                    touches_border = True

                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = row + drow
                    next_col = col + dcol
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if seen[next_row][next_col] or grid[next_row][next_col] != 0:
                        continue
                    seen[next_row][next_col] = True
                    queue.append((next_row, next_col))

            if not touches_border:
                enclosed.append(component)

    enclosed.sort(key=len)
    for component, color in zip(enclosed, (8, 4, 3)):
        for row, col in component:
            result[row][col] = color

    return result
