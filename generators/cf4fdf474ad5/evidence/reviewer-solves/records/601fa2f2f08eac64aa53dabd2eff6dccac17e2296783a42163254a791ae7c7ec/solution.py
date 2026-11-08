from collections import deque


def solve(grid):
    """Extract the lower-left 4-connected nonzero component."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    seen = set()
    boxes = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            min_row = max_row = row
            min_col = max_col = col

            while queue:
                current_row, current_col = queue.popleft()
                min_row = min(min_row, current_row)
                max_row = max(max_row, current_row)
                min_col = min(min_col, current_col)
                max_col = max(max_col, current_col)

                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 0:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            boxes.append((min_row, min_col, max_row, max_col))

    if not boxes:
        return []

    # Prefer the lowest component; among components beginning on the same row,
    # prefer the leftmost one.
    min_row, min_col, max_row, max_col = max(
        boxes, key=lambda box: (box[0], -box[1])
    )
    return [
        row[min_col : max_col + 1]
        for row in grid[min_row : max_row + 1]
    ]
