from collections import deque


def solve(grid):
    """Return the widest monochrome object, cropped and recolored azure (8)."""
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

            min_row = min(r for r, _ in cells)
            max_row = max(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            max_col = max(c for _, c in cells)
            objects.append((max_col - min_col + 1, cells, min_row, max_row, min_col, max_col))

    if not objects:
        return []

    _, cells, min_row, max_row, min_col, max_col = max(objects, key=lambda item: item[0])
    selected = set(cells)
    return [
        [8 if (row, col) in selected else 0 for col in range(min_col, max_col + 1)]
        for row in range(min_row, max_row + 1)
    ]
