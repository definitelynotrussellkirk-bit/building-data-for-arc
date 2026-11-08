"""Visible-example hypothesis: recolor singleton colored objects to 9."""


def solve(grid):
    result = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            has_same_color_neighbor = any(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == color
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if not has_same_color_neighbor:
                result[row][col] = 9
    return result
