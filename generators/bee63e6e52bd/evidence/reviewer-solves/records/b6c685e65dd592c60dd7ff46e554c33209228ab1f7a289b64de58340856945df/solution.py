"""Opening-aligned yellow fill inferred from the public examples."""


def solve(grid):
    result = [list(row) for row in grid]
    occupied = [(r, c) for r, row in enumerate(grid)
                for c, color in enumerate(row) if color != 0]
    if not occupied:
        return result

    top = min(r for r, c in occupied)
    bottom = max(r for r, c in occupied)
    left = min(c for r, c in occupied)
    right = max(c for r, c in occupied)
    side_gaps = {
        "top": [c for c in range(left, right + 1) if grid[top][c] == 0],
        "bottom": [c for c in range(left, right + 1) if grid[bottom][c] == 0],
        "left": [r for r in range(top, bottom + 1) if grid[r][left] == 0],
        "right": [r for r in range(top, bottom + 1) if grid[r][right] == 0],
    }
    open_sides = [(side, gap) for side, gap in side_gaps.items() if gap]
    if len(open_sides) != 1:
        raise ValueError("The examples specify one open side of a rectangular frame")
    side, gap = open_sides[0]
    low, high = min(gap), max(gap)
    if gap != list(range(low, high + 1)):
        raise ValueError("The examples specify one contiguous opening")

    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                continue
            if side == "top":
                outward, transverse = top - r, c
            elif side == "bottom":
                outward, transverse = r - bottom, c
            elif side == "left":
                outward, transverse = left - c, r
            else:
                outward, transverse = c - right, r

            inside_frame = top < r < bottom and left < c < right
            interior_band = inside_frame and low - 1 <= transverse <= high + 1
            straight_beam = outward >= 0 and low <= transverse <= high
            diagonal_rays = (outward > 0
                             and transverse in (low - outward, high + outward))
            if interior_band or straight_beam or diagonal_rays:
                result[r][c] = 4
    return result
