from __future__ import annotations


def solve(grid):
    """Keep nonzero 4-connected components that touch the outer frame."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue

            stack = [(row0, col0)]
            seen.add((row0, col0))
            component = []
            touches_border = False

            while stack:
                row, col = stack.pop()
                component.append((row, col))
                if row in (0, height - 1) or col in (0, width - 1):
                    touches_border = True
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row, next_col = row + drow, col + dcol
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            if touches_border:
                for row, col in component:
                    output[row][col] = color

    return output
