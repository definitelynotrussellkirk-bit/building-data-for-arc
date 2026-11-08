from collections import defaultdict

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]

    centers = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if all(grid[row + dr][col + dc] == 2 for dr, dc in _CARDINAL):
                centers.append((row, col))

    by_row = defaultdict(list)
    by_col = defaultdict(list)
    for row, col in centers:
        by_row[row].append(col)
        by_col[col].append(row)

    for row, columns in by_row.items():
        ordered = sorted(set(columns))
        for left, right in zip(ordered, ordered[1:]):
            for col in range(left + 1, right):
                if output[row][col] == 0:
                    output[row][col] = 1

    for col, rows in by_col.items():
        ordered = sorted(set(rows))
        for top, bottom in zip(ordered, ordered[1:]):
            for row in range(top + 1, bottom):
                if output[row][col] == 0:
                    output[row][col] = 1

    return output
