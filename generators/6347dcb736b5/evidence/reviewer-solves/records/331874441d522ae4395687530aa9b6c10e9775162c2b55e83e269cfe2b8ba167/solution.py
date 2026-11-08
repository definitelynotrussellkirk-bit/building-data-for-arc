from __future__ import annotations


def solve(grid):
    """Replace each nonzero 4-connected component by its bbox perimeter."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_col = current_row + dr, current_col + dc
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            row1, row2 = min(rows), max(rows)
            col1, col2 = min(cols), max(cols)
            for r in range(row1, row2 + 1):
                for c in range(col1, col2 + 1):
                    if r in (row1, row2) or c in (col1, col2):
                        output[r][c] = color

    return output
