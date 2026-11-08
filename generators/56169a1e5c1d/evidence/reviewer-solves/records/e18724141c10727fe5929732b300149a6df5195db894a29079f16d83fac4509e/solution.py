from collections import defaultdict


def solve(grid):
    """Fill the midpoint of each same-color 2-by-2 diagonal endpoint pair."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    by_color = defaultdict(list)
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color != 0:
                by_color[color].append((row, col))

    additions = {}
    for color, cells in by_color.items():
        for index, (row_a, col_a) in enumerate(cells):
            for row_b, col_b in cells[index + 1 :]:
                if abs(row_a - row_b) != 2 or abs(col_a - col_b) != 2:
                    continue
                mid_row = (row_a + row_b) // 2
                mid_col = (col_a + col_b) // 2
                if grid[mid_row][mid_col] != 0:
                    continue
                previous = additions.get((mid_row, mid_col))
                if previous is None or previous == color:
                    additions[(mid_row, mid_col)] = color

    for (row, col), color in additions.items():
        result[row][col] = color
    return result
