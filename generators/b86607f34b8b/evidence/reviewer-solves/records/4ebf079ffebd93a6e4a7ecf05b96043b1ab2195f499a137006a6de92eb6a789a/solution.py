"""Exposed visible-example solve. No imports from the generator or authority."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    divider = next(i for i, row in enumerate(grid) if set(row) == {9})

    def horizontal(points):
        filled = set(points)
        for row in range(divider + 1, height):
            columns = [column for r, column in points if r == row]
            if columns:
                filled.update((row, column)
                              for column in range(min(columns), max(columns) + 1))
        return filled

    def vertical(points):
        filled = set(points)
        for column in range(width):
            rows = [row for row, c in points if c == column]
            if rows:
                filled.update((row, column)
                              for row in range(min(rows), max(rows) + 1))
        return filled

    answer = [row[:] if i <= divider else [0] * width
              for i, row in enumerate(grid)]
    claims = {}
    for column, color in enumerate(grid[0]):
        if color == 0:
            continue
        operation = grid[1][column]
        original = {(row, col) for row in range(divider + 1, height)
                    for col in range(width) if grid[row][col] == color}
        if operation == 1:
            painted = horizontal(original)
        elif operation == 2:
            painted = vertical(original)
        elif operation == 3:
            painted = vertical(horizontal(original))
        elif operation == 4:
            painted = horizontal(original) - original
        else:
            raise ValueError('unrecognized legend operation')
        strength = ({1: 4, 3: 3, 2: 2, 4: 1}[operation], color)
        for point in painted:
            if point not in claims or strength > claims[point]:
                claims[point] = strength
                answer[point[0]][point[1]] = color
    return answer
