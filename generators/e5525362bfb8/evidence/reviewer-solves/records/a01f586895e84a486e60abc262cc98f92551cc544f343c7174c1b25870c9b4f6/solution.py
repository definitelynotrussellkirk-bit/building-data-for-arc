"""Connect diagonally aligned green plus centers through background cells."""


def solve(grid):
    result = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    centers = [
        (r, c)
        for r in range(1, height - 1)
        for c in range(1, width - 1)
        if all(
            grid[r + dr][c + dc] == 3
            for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
        )
    ]

    for index, (r1, c1) in enumerate(centers):
        for r2, c2 in centers[index + 1:]:
            dr, dc = r2 - r1, c2 - c1
            if dr == 0 or abs(dr) != abs(dc):
                continue
            step_r = 1 if dr > 0 else -1
            step_c = 1 if dc > 0 else -1
            for distance in range(1, abs(dr)):
                r = r1 + distance * step_r
                c = c1 + distance * step_c
                if grid[r][c] == 0:
                    result[r][c] = 2
    return result
