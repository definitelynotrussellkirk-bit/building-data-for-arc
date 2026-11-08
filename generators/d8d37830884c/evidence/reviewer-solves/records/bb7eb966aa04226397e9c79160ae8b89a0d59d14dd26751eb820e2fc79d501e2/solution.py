"""Visible-example solution for d8d37830884c."""


def solve(grid):
    """Recolour 4-connected nonzero objects by cardinality.

    Objects with exactly six cells become red (2); every other nonzero object
    becomes blue (1). Background remains black (0).
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    height = len(grid)
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            cells = []
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            replacement = 2 if len(cells) == 6 else 1
            for row, col in cells:
                output[row][col] = replacement

    return output
