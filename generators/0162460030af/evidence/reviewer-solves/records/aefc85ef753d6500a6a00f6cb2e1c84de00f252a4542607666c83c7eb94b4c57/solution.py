"""Visible-example solution for ARC task 0162460030af."""


def _components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    found = []

    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(cells)
    return found


def solve(grid):
    """Recolor foreground components in horizontal order, anchored by 8 at right."""
    output = [row[:] for row in grid]
    components = sorted(_components(grid), key=lambda cells: min(c for _, c in cells))
    count = len(components)
    for index, cells in enumerate(components):
        # Moving left from the rightmost component alternates 8, 2, 8, 2, ...
        color = 8 if (count - 1 - index) % 2 == 0 else 2
        for row, column in cells:
            output[row][column] = color
    return output
