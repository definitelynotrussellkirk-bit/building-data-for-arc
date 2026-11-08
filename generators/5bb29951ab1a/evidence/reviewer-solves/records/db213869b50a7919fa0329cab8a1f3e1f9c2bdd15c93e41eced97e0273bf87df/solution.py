from collections import Counter


def solve(grid):
    """Remove the sparse corruption color and restore the underlying block grid."""
    counts = Counter(cell for row in grid for cell in row if cell != 0)
    if not counts:
        return [row[:] for row in grid]

    fill = counts.most_common(1)[0][0]
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, fill):
                continue

            fill_neighbors = 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == fill:
                    fill_neighbors += 1

            # A damaged cell within a solid rectangle, or in a one-cell gap
            # directly joining two rectangles, has support from at least two
            # orthogonal fill neighbours.  Stray damage on borders/background
            # has at most one such neighbour.
            out[r][c] = fill if fill_neighbors >= 2 else 0

    return out
