def solve(grid):
    """Join cyan anchors that share a row or column."""
    output = [row[:] for row in grid]
    if not output:
        return output

    height = len(output)
    width = len(output[0])

    for row in range(height):
        anchors = [col for col, value in enumerate(grid[row]) if value == 8]
        if len(anchors) >= 2:
            for col in range(min(anchors), max(anchors) + 1):
                if output[row][col] == 0:
                    output[row][col] = 8

    for col in range(width):
        anchors = [row for row in range(height) if grid[row][col] == 8]
        if len(anchors) >= 2:
            for row in range(min(anchors), max(anchors) + 1):
                if output[row][col] == 0:
                    output[row][col] = 8

    return output
