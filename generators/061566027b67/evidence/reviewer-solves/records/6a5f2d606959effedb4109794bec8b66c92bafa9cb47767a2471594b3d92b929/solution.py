from __future__ import annotations


def solve(grid):
    """Keep the largest solid nonzero rectangle and erase all other cells."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    best = None  # (area, min_side, -top, -left, color, top, left, bottom, right)

    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        # For every top/bottom pair, track columns that are solid in all rows.
        for top in range(h):
            solid = [True] * w
            for bottom in range(top, h):
                for col in range(w):
                    solid[col] = solid[col] and grid[bottom][col] == color

                run_start = None
                for col in range(w + 1):
                    is_solid = col < w and solid[col]
                    if is_solid and run_start is None:
                        run_start = col
                    elif not is_solid and run_start is not None:
                        left = run_start
                        right = col - 1
                        height = bottom - top + 1
                        width = right - left + 1
                        # The signal in the examples is a genuine 2-D block,
                        # not a chance one-cell-wide run in the noise.
                        if height >= 2 and width >= 2:
                            area = height * width
                            candidate = (
                                area,
                                min(height, width),
                                -top,
                                -left,
                                color,
                                top,
                                left,
                                bottom,
                                right,
                            )
                            if best is None or candidate > best:
                                best = candidate
                        run_start = None

    out = [[0 for _ in range(w)] for _ in range(h)]
    if best is None:
        return out

    _, _, _, _, color, top, left, bottom, right = best
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            out[row][col] = color
    return out
