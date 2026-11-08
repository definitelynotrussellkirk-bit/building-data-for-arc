"""Visible-example solution for the blind ARC episode."""


def solve(grid):
    """Project a cross from each colored marker until a gray wall or edge.

    Gray cells (5) are walls.  Every other nonzero input cell is a marker.
    Markers keep their original color.  Empty cells reached by one marker take
    that marker's color; cells reached by two or more markers become 8.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    markers = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value not in (0, 5):
                markers.append((row, col, value))

    hits = [[set() for _ in range(width)] for _ in range(height)]
    for marker_id, (row, col, _value) in enumerate(markers):
        # The horizontal and vertical spans are independently bounded by gray.
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = row, col
            while 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 5:
                hits[rr][cc].add(marker_id)
                rr += dr
                cc += dc

    marker_positions = {(row, col) for row, col, _ in markers}
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 or (row, col) in marker_positions:
                continue
            reaching = hits[row][col]
            if len(reaching) == 1:
                marker_id = next(iter(reaching))
                out[row][col] = markers[marker_id][2]
            elif len(reaching) >= 2:
                out[row][col] = 8

    return out
