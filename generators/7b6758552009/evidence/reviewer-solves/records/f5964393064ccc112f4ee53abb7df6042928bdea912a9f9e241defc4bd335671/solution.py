"""Visible-example solution for ARC task 7b6758552009."""


def solve(grid):
    """Return one row listing object colors from left to right.

    A non-background object is a 4-connected component of a single color.
    Objects are ordered by their leftmost occupied column, then by their
    topmost row to resolve the only visible tie pattern.
    """
    if not grid or not grid[0]:
        return [[]]

    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            min_row = row
            min_col = col

            while stack:
                current_row, current_col = stack.pop()
                min_row = min(min_row, current_row)
                min_col = min(min_col, current_col)

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
                    stack.append((next_row, next_col))

            objects.append((min_col, min_row, color))

    objects.sort()
    return [[color for _, _, color in objects]]
