from collections import deque


COLOR_ORDER = (5, 2, 8, 9, 6)
BACKGROUND = 7


def _component_count(grid, color):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    seen = set()
    count = 0

    for row in range(rows):
        for col in range(cols):
            if grid[row][col] != color or (row, col) in seen:
                continue

            count += 1
            seen.add((row, col))
            queue = deque([(row, col)])
            while queue:
                current_row, current_col = queue.popleft()
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < rows and 0 <= next_col < cols):
                        continue
                    position = (next_row, next_col)
                    if position in seen or grid[next_row][next_col] != color:
                        continue
                    seen.add(position)
                    queue.append(position)

    return count


def solve(grid):
    heights = [_component_count(grid, color) for color in COLOR_ORDER]
    output_height = max(heights, default=0)
    return [
        [
            color if height >= output_height - row else BACKGROUND
            for color, height in zip(COLOR_ORDER, heights)
        ]
        for row in range(output_height)
    ]
