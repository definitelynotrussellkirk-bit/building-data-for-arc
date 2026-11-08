"""Visible-example hypothesis: rotate all colours clockwise about the sole 9."""


def solve(grid):
    if not grid or not grid[0]:
        raise ValueError("Expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")
    anchors = [(r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 9]
    if len(anchors) != 1:
        raise ValueError("Expected one colour-9 rotation centre")
    pr, pc = anchors[0]
    output = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            nr, nc = pr + (c - pc), pc - (r - pr)
            if not (0 <= nr < height and 0 <= nc < width):
                raise ValueError("Rotated foreground does not fit the input canvas")
            output[nr][nc] = value
    return output
