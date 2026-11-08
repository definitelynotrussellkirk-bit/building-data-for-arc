from collections import Counter


def solve(grid):
    """Keep cells that participate in a same-colour diagonal run."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    result = [[background for _ in range(width)] for _ in range(height)]

    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == background:
                continue
            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                rr, cc = row + dr, col + dc
                if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == colour:
                    result[row][col] = colour
                    break

    return result
