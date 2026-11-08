def solve(grid):
    """Match the complete corner key, then return the oriented whole panel."""
    blue = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 1]
    if not blue:
        raise ValueError("Missing blue panel")
    top = min(r for r, c in blue)
    bottom = max(r for r, c in blue)
    left = min(c for r, c in blue)
    right = max(c for r, c in blue)
    panel = [row[left:right + 1] for row in grid[top:bottom + 1]]
    dots = {(r, c): value for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value != 0 and not (top <= r <= bottom and left <= c <= right)}
    if len(dots) != 3:
        raise ValueError("Expected three external key dots")
    key_top = min(r for r, c in dots)
    key_bottom = max(r for r, c in dots)
    key_left = min(c for r, c in dots)
    key_right = max(c for r, c in dots)
    key = tuple(dots.get(point, 1) for point in (
        (key_top, key_left), (key_top, key_right),
        (key_bottom, key_left), (key_bottom, key_right)))

    def turn_clockwise(matrix):
        height, width = len(matrix), len(matrix[0])
        return [[matrix[height - 1 - c][r] for c in range(height)]
                for r in range(width)]

    def corner_roles(matrix):
        return (matrix[1][1], matrix[1][-2],
                matrix[-2][1], matrix[-2][-2])

    matches = []
    for reflected in (False, True):
        candidate = [row[::-1] if reflected else row[:] for row in panel]
        for _ in range(4):
            if corner_roles(candidate) == key:
                matches.append(candidate)
            candidate = turn_clockwise(candidate)
    if len(matches) != 1:
        raise ValueError("Corner key does not specify one orientation")
    return matches[0]
