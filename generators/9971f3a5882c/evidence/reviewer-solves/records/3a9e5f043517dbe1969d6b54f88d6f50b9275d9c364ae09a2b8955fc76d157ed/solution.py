"""Visible-example implementation of the marker-guided lattice transform."""


def solve(grid):
    h, w = len(grid), len(grid[0])
    lattice = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6]
    if not lattice:
        raise ValueError("Expected a green lattice")
    top = min(r for r, _ in lattice)
    bottom = max(r for r, _ in lattice)
    left = min(c for _, c in lattice)
    right = max(c for _, c in lattice)
    horizontal = [r for r in range(top, bottom + 1)
                  if all(grid[r][c] == 3 for c in range(left, right + 1))]
    vertical = [c for c in range(left, right + 1)
                if all(grid[r][c] == 3 for r in range(top, bottom + 1))]

    above = [r for r, c in markers if r < top and left <= c <= right]
    below = [r for r, c in markers if r > bottom and left <= c <= right]
    before = [c for r, c in markers if c < left]
    after = [c for r, c in markers if c > right]
    target_top = max(above) + 1 if above else top
    target_bottom = min(below) - 1 if below else bottom
    target_left = max(before) + 1 if before else left
    target_right = min(after) - 1 if after else right

    result = [[0] * w for _ in range(h)]
    for r in horizontal:
        rr = target_top if r == top else target_bottom if r == bottom else r
        for c in range(target_left, target_right + 1):
            result[rr][c] = 3
    for c in vertical:
        cc = target_left if c == left else target_right if c == right else c
        for r in range(target_top, target_bottom + 1):
            result[r][cc] = 3
    for r, c in markers:
        result[r][c] = 6
    return result
