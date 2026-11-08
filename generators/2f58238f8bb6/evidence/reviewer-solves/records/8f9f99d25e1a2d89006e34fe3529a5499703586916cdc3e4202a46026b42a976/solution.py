"""Reproduce the visible command sequence with transformed object copies."""


def solve(grid):
    commands = [value for value in grid[0] if value != 0]
    cells = [
        (row, column)
        for row in range(1, len(grid))
        for column, value in enumerate(grid[row])
        if value != 0
    ]
    if not commands or not cells:
        raise ValueError("Expected a top-row command sequence and an object below it")

    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(column for _, column in cells)
    right = max(column for _, column in cells)
    original = [list(row[left : right + 1]) for row in grid[top : bottom + 1]]

    def transform(command):
        if command == 1:
            return [row[:] for row in original]
        if command == 2:
            return [list(row) for row in zip(*original[::-1])]
        if command == 3:
            return [row[::-1] for row in original[::-1]]
        if command == 4:
            return [row[::-1] for row in original]
        raise ValueError("Unknown transformation command")

    copies = [transform(command) for command in commands]
    height = max(len(copy) for copy in copies)
    width = sum(len(copy[0]) for copy in copies) + len(copies) - 1
    output = [[0] * width for _ in range(height)]
    offset = 0
    for copy in copies:
        copy_width = len(copy[0])
        for row, values in enumerate(copy):
            output[row][offset : offset + copy_width] = values
        offset += copy_width + 1
    return output
