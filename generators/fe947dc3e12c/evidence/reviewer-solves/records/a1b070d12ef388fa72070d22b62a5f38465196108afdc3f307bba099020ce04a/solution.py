from collections import deque


def solve(grid):
    """Recolor the three objects by increasing/decreasing area rank."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            color = grid[row][col]
            cells = []
            queue = deque([(row, col)])
            seen.add((row, col))

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

            objects.append(cells)

    objects.sort(key=lambda cells: (len(cells), cells[0]))
    for index, cells in enumerate(objects):
        if index == 0:
            replacement = 2
        elif index == len(objects) - 1:
            replacement = 1
        else:
            replacement = 4
        for row, col in cells:
            output[row][col] = replacement

    return output
