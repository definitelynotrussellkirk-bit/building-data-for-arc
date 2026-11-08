from collections import Counter, deque


def _components(grid, background):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            cells = []
            queue = deque([(row, col)])
            seen.add((row, col))
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
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            components.append((color, cells))

    return components


def solve(grid):
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    result = [row[:] for row in grid]
    components = _components(grid, background)

    moving = [(color, cells) for color, cells in components if len(cells) >= 4]
    for _, cells in moving:
        for row, col in cells:
            result[row][col] = background

    for color, cells in moving:
        bottom = max(row for row, _ in cells)
        offset = height - 1 - bottom
        for row, col in cells:
            result[row + offset][col] = color

    return result
