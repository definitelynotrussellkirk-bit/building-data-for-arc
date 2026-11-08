"""Visible-only ARC solution for task a0c6005765ee."""


def solve(grid):
    """Fill the interior line indicated by each red marker.

    A red 7 sits immediately outside a gray (5) rectangular frame.  Starting
    from the adjacent gray side cell, continue straight through the frame and
    recolor the zero-valued interior cells green (3) until the opposite gray
    side is reached.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 7:
                continue

            candidates = []
            for dr, dc in directions:
                br, bc = r + dr, c + dc
                if not (0 <= br < height and 0 <= bc < width):
                    continue
                if grid[br][bc] != 5:
                    continue

                cells = []
                rr, cc = br + dr, bc + dc
                while 0 <= rr < height and 0 <= cc < width:
                    if grid[rr][cc] == 5:
                        if cells:
                            candidates.append((len(cells), cells))
                        break
                    if grid[rr][cc] != 0:
                        break
                    cells.append((rr, cc))
                    rr += dr
                    cc += dc

            if candidates:
                # A well-formed task has one ray.  Prefer the longest valid
                # framed span if a marker happens to touch more than one side.
                _, cells = max(candidates, key=lambda item: item[0])
                for rr, cc in cells:
                    out[rr][cc] = 3

    return out
