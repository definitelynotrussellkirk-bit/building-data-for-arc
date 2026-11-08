from collections import deque


def solve(grid):
    """Recolor the red-count-selected nested gray frame azure.

    The gray frames are separate 4-connected components.  Red cells encode a
    one-based index from the outside, so sorting frame components by bounding
    box area (largest first) identifies the selected frame without assuming
    fixed spacing or dimensions.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    red_count = sum(cell == 2 for row in grid for cell in row)
    if red_count <= 0:
        return result

    seen = [[False] * width for _ in range(height)]
    frames = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 4 or seen[row][col]:
                continue

            queue = deque([(row, col)])
            seen[row][col] = True
            cells = []
            min_row = max_row = row
            min_col = max_col = col

            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                min_row = min(min_row, current_row)
                max_row = max(max_row, current_row)
                min_col = min(min_col, current_col)
                max_col = max(max_col, current_col)

                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if seen[next_row][next_col] or grid[next_row][next_col] != 4:
                        continue
                    seen[next_row][next_col] = True
                    queue.append((next_row, next_col))

            box_area = (max_row - min_row + 1) * (max_col - min_col + 1)
            frames.append((box_area, len(cells), cells))

    frames.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected_index = red_count - 1
    if selected_index >= len(frames):
        return result

    for row, col in frames[selected_index][2]:
        result[row][col] = 8

    return result
