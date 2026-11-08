from collections import deque


def solve(grid):
    """Crop the largest 4-connected nonzero monochrome object.

    Ties are resolved by the object's top-left position in reading order.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
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

            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            objects.append((len(cells), top, left, color, cells))

    if not objects:
        return []

    _, top, left, color, cells = min(objects, key=lambda obj: (-obj[0], obj[1], obj[2]))
    bottom = max(r for r, _ in cells)
    right = max(c for _, c in cells)
    output = [[0 for _ in range(right - left + 1)] for _ in range(bottom - top + 1)]
    for row, col in cells:
        output[row - top][col - left] = color
    return output
