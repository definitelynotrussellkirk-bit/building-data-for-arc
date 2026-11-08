"""Visible-example solution for the generated b88894a36787 episode."""


def solve(grid):
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    headers = [(col, color) for col, color in enumerate(grid[0]) if color != 0]
    body = [
        (row, col, grid[row][col])
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] != 0
    ]

    entries = []
    for header_col, color in headers:
        target = next((dot for dot in body if dot[2] == color), None)
        if target is None:
            entries.append((header_col, color, height - 1, None))
        else:
            entries.append((header_col, color, target[0], target[1]))

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            for header_col, color, target_row, target_col in entries:
                on_vertical = col == header_col and row <= target_row
                on_horizontal = (
                    target_col is not None
                    and row == target_row
                    and min(header_col, target_col) <= col <= max(header_col, target_col)
                )
                if on_vertical or on_horizontal:
                    output[row][col] = color
                    break
    return output
