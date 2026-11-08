def solve(grid):
    """Connect unobstructed pairs of red (2) cells with azure (8) lines."""
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height = len(source)
    width = len(source[0]) if height else 0

    # Join consecutive red endpoints in each row when every intervening cell is empty.
    for row in range(height):
        endpoints = [col for col in range(width) if source[row][col] == 2]
        for left, right in zip(endpoints, endpoints[1:]):
            if all(source[row][col] == 0 for col in range(left + 1, right)):
                for col in range(left + 1, right):
                    output[row][col] = 8

    # Join consecutive red endpoints in each column under the same visibility rule.
    for col in range(width):
        endpoints = [row for row in range(height) if source[row][col] == 2]
        for top, bottom in zip(endpoints, endpoints[1:]):
            if all(source[row][col] == 0 for row in range(top + 1, bottom)):
                for row in range(top + 1, bottom):
                    output[row][col] = 8

    return output
