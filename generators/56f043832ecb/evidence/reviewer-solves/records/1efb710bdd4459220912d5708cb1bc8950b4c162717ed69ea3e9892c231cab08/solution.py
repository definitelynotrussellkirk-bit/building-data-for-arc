from collections import deque


def solve(grid):
    """Fill the interiors of complete monochrome rectangular frames."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            top = min(position[0] for position in component)
            bottom = max(position[0] for position in component)
            left = min(position[1] for position in component)
            right = max(position[1] for position in component)
            if bottom - top < 2 or right - left < 2:
                continue

            perimeter = (
                [(top, current_col) for current_col in range(left, right + 1)]
                + [(bottom, current_col) for current_col in range(left, right + 1)]
                + [(current_row, left) for current_row in range(top + 1, bottom)]
                + [(current_row, right) for current_row in range(top + 1, bottom)]
            )
            if not all(grid[current_row][current_col] == color for current_row, current_col in perimeter):
                continue

            for current_row in range(top + 1, bottom):
                for current_col in range(left + 1, right):
                    out[current_row][current_col] = color

    return out
