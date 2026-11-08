def solve(grid):
    result = [list(row) for row in grid]
    for r, row in enumerate(grid):
        if row and all(value in (1, 2, 8) for value in row):
            for c, value in enumerate(row):
                if value not in (2, 8):
                    continue
                height = 4 if value == 2 else 3
                for offset in range(1, height + 1):
                    rr = r - offset
                    if rr >= 0:
                        result[rr][c] = value if offset == height else 1
            return result
    return result
