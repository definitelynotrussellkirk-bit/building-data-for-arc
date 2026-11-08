from collections import deque


def solve(grid):
    """Recolor every 4-connected nonzero object touching the border to 7."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            component = []
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            touches_border = False

            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                touches_border |= (
                    row == 0
                    or row == height - 1
                    or col == 0
                    or col == width - 1
                )

                for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = row + d_row
                    next_col = col + d_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            if touches_border:
                for row, col in component:
                    result[row][col] = 7

    return result
