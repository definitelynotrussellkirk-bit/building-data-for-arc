"""Visible-example solution for the blind ARC episode.

Blue (1) pillars initiate a rightward domino chain.  A fallen pillar can
knock over the next pillar when its column is at most three cells to the
right.  Fallen pillars are replaced by a three-cell horizontal bar on the
bottom row; upright pillars are left unchanged.
"""


def solve(grid):
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    bottom = height - 1

    # The examples contain bottom-anchored monochrome vertical pillars.
    pillars = []
    for col in range(width):
        cells = [grid[row][col] for row in range(height) if grid[row][col] != 0]
        if cells:
            pillars.append((col, grid[bottom][col] or cells[-1]))

    fallen = set()
    active_reach = -1
    for col, color in pillars:
        if color == 1 or col <= active_reach:
            fallen.add(col)
            active_reach = max(active_reach, col + 3)

    out = [row[:] for row in grid]
    colors = dict(pillars)

    # Remove the vertical forms first.
    for col in fallen:
        for row in range(height):
            if out[row][col] != 0:
                out[row][col] = 0

    # Draw from left to right so every pillar keeps its own pivot color when
    # two fallen bars overlap.
    for col in sorted(fallen):
        color = colors[col]
        for x in range(col, min(width, col + 3)):
            out[bottom][x] = color

    return out
