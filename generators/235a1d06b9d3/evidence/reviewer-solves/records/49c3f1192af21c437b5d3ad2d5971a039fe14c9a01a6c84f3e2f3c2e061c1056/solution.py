from collections import Counter


def solve(grid):
    """Keep the two header rows and project row 0's marks into color 6."""
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    projected = [6 if cell != background else background for cell in grid[0]]
    return [list(grid[0]), list(grid[1]), projected]
