from collections import Counter


def solve(grid):
    """Fill each region's background holes with the next region's color."""
    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    separator_columns = {
        col for col in range(width)
        if all(grid[row][col] == background for row in range(height))
    }

    regions = []
    current = []
    for col in range(width):
        if col in separator_columns:
            if current:
                regions.append(current)
                current = []
        else:
            current.append(col)
    if current:
        regions.append(current)

    region_colors = []
    for columns in regions:
        colors = {
            grid[row][col]
            for row in range(height)
            for col in columns
            if grid[row][col] != background
        }
        if len(colors) != 1:
            raise ValueError("each region must have exactly one non-background color")
        region_colors.append(next(iter(colors)))

    result = [row[:] for row in grid]
    for index, columns in enumerate(regions):
        replacement = region_colors[(index + 1) % len(regions)]
        for row in range(height):
            for col in columns:
                if grid[row][col] == background:
                    result[row][col] = replacement
    return result
