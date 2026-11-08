from collections import deque


def solve(grid):
    """Crop nonzero 4-components and pack them by original (left, top)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue

            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row, next_col = row + dr, col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] == 0:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            top = min(row for row, _ in cells)
            bottom = max(row for row, _ in cells)
            left = min(col for _, col in cells)
            right = max(col for _, col in cells)
            crop = [
                source_row[left : right + 1]
                for source_row in grid[top : bottom + 1]
            ]
            components.append((left, top, crop))

    components.sort(key=lambda item: (item[0], item[1]))
    if not components:
        return [[0]]

    output_height = max(len(crop) for _, _, crop in components)
    output_width = sum(len(crop[0]) for _, _, crop in components) + len(components) - 1
    output = [[0 for _ in range(output_width)] for _ in range(output_height)]

    output_left = 0
    for _, _, crop in components:
        for row, values in enumerate(crop):
            for col, value in enumerate(values):
                if value != 0:
                    output[row][output_left + col] = value
        output_left += len(crop[0]) + 1

    return output
