"""Visible-example solution for ARC task 521473faec65."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    point = (next_row, next_col)
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and point not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add(point)
                        queue.append(point)

            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            for r in range(top, bottom + 1):
                for c in range(left, right + 1):
                    if (r - top + c - left) % 2 == 0:
                        output[r][c] = color

    return output
