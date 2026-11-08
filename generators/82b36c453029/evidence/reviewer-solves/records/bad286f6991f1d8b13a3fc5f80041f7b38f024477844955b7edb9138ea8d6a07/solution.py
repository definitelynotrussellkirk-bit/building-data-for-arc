"""Visible-example solution for reviewer-authored ARC task 82b36c453029."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells = []
            while stack:
                current_row, current_column = stack.pop()
                cells.append((current_row, current_column))
                for drow, dcolumn in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + drow
                    next_column = current_column + dcolumn
                    if (
                        0 <= next_row < height
                        and 0 <= next_column < width
                        and (next_row, next_column) not in seen
                        and grid[next_row][next_column] == color
                    ):
                        seen.add((next_row, next_column))
                        stack.append((next_row, next_column))

            rows = [r for r, _ in cells]
            columns = [c for _, c in cells]
            center_row = (min(rows) + max(rows)) // 2
            center_column = (min(columns) + max(columns)) // 2
            output[center_row][center_column] = color

    return output
