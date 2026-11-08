"""Fresh Python solve written from the exposed post-repair visible episode."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    key_end = max(i for i, color in enumerate(grid[0]) if color != 0) + 1
    key = grid[0][:key_end]
    seed = [(r, c) for r in range(2, height) for c in range(width) if grid[r][c] != 0]
    if len(seed) != 1:
        raise ValueError("expected one point below the separator")
    center_r, center_c = seed[0]
    result = [row[:] for row in grid]
    for r in range(2, height):
        for c in range(width):
            radius = max(abs(r-center_r), abs(c-center_c))
            if radius < len(key):
                result[r][c] = key[radius]
    for radius, color in enumerate(key):
        fully_inside = (center_r-radius >= 2 and center_r+radius < height
                        and center_c-radius >= 0 and center_c+radius < width)
        if color != 0 and not fully_inside:
            result[0][radius] = 5
    return result
