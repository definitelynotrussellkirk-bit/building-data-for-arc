from collections import deque


def solve(grid):
    """Pack the non-background objects from largest to smallest.

    Each 4-connected nonzero object is cropped to its bounding box.  Crops are
    placed at the top of a common canvas with one blank column between them.
    Equal-size objects are ordered by their color, matching both visible ties.
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

            top = min(row for row, _ in cells)
            bottom = max(row for row, _ in cells)
            left = min(col for _, col in cells)
            right = max(col for _, col in cells)
            crop = [
                [grid[crop_row][crop_col] for crop_col in range(left, right + 1)]
                for crop_row in range(top, bottom + 1)
            ]
            objects.append((len(cells), color, crop))

    objects.sort(key=lambda item: (-item[0], item[1]))
    if not objects:
        return []

    output_height = max(len(crop) for _, _, crop in objects)
    output_width = sum(len(crop[0]) for _, _, crop in objects) + len(objects) - 1
    output = [[0] * output_width for _ in range(output_height)]

    offset = 0
    for _, _, crop in objects:
        for crop_row, values in enumerate(crop):
            output[crop_row][offset : offset + len(values)] = values
        offset += len(crop[0]) + 1

    return output
