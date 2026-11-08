from collections import deque


def solve(grid):
    """Recolor every colored component orthogonally touching color 1 to color 4."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    marker = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }

    seen = set()
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color in (0, 1) or (start_row, start_col) in seen:
                continue

            component = []
            touches_marker = False
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))

            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                for drow, dcol in directions:
                    next_row, next_col = row + drow, col + dcol
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in marker:
                        touches_marker = True
                    elif (
                        grid[next_row][next_col] == color
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))

            if touches_marker:
                for row, col in component:
                    result[row][col] = 4

    return result
