from collections import Counter


def solve(grid):
    """Move each tiny monochrome L to its orientation-matching output corner."""
    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    output = [[background for _ in range(width)] for _ in range(height)]

    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    }
    components = []
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        stack = [start]
        cells = [start]
        while stack:
            row, col = stack.pop()
            for next_row, next_col in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                point = (next_row, next_col)
                if point in unseen and grid[next_row][next_col] == color:
                    unseen.remove(point)
                    stack.append(point)
                    cells.append(point)
        components.append((color, cells))

    arm = (height - 1) // 2
    shapes = {
        frozenset({(0, 0), (0, 1), (1, 0)}): "top_left",
        frozenset({(0, 0), (0, 1), (1, 1)}): "top_right",
        frozenset({(0, 0), (1, 0), (1, 1)}): "bottom_left",
        frozenset({(0, 1), (1, 0), (1, 1)}): "bottom_right",
    }

    for color, cells in components:
        top = min(row for row, _ in cells)
        left = min(col for _, col in cells)
        shape = frozenset((row - top, col - left) for row, col in cells)
        corner = shapes[shape]

        if corner == "top_left":
            for offset in range(arm):
                output[0][offset] = color
                output[offset][0] = color
        elif corner == "top_right":
            for offset in range(arm):
                output[0][width - 1 - offset] = color
                output[offset][width - 1] = color
        elif corner == "bottom_left":
            for offset in range(arm):
                output[height - 1][offset] = color
                output[height - 1 - offset][0] = color
        else:
            for offset in range(arm):
                output[height - 1][width - 1 - offset] = color
                output[height - 1 - offset][width - 1] = color

    return output
