def solve(grid):
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        nonzero = [c for c, value in enumerate(row) if value != 0]
        if len(nonzero) != 2:
            continue
        left, right = nonzero
        if row[left] != 5 or row[right] != 5:
            continue
        for c in range(left + 1, right):
            result[r][c] = 3
    return result
