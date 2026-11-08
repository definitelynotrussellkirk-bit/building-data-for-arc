from collections import Counter


def solve(grid):
    """Remove the sparse noise color while restoring interrupted solid regions."""
    counts = Counter(value for row in grid for value in row if value != 0)
    if len(counts) < 2:
        return [row[:] for row in grid]

    fill = max(counts, key=counts.get)
    noise = {value for value in counts if value != fill}
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            if grid[row][col] not in noise:
                continue
            neighbors = 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = row + dr, col + dc
                if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == fill:
                    neighbors += 1
            result[row][col] = fill if neighbors >= 2 else 0

    return result
