"""Visible-example solution for the blind ARC episode.

The colored interior cells are sites of a Manhattan-distance Voronoi diagram.
Every interior cell receives the color of its unique closest site; cells tied
between differently colored closest sites become color 8.  The frame is kept.
"""


def solve(grid):
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    frame = grid[0][0]
    background = 0

    sites = [
        (row, col, grid[row][col])
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] not in (background, frame)
    ]

    result = [row[:] for row in grid]
    if not sites:
        return result

    for row in range(1, height - 1):
        for col in range(1, width - 1):
            distances = [
                (abs(row - site_row) + abs(col - site_col), color)
                for site_row, site_col, color in sites
            ]
            nearest_distance = min(distance for distance, _ in distances)
            nearest_colors = {
                color for distance, color in distances if distance == nearest_distance
            }
            result[row][col] = (
                next(iter(nearest_colors)) if len(nearest_colors) == 1 else 8
            )

    return result
