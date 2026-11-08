def solve(grid):
    """Crop to the bounding box of the non-key cells matching the top-left key."""
    if not grid or not grid[0]:
        return []

    key = grid[0][0]
    points = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == key and (row, col) != (0, 0)
    ]
    if not points:
        return []

    top = min(row for row, _ in points)
    bottom = max(row for row, _ in points)
    left = min(col for _, col in points)
    right = max(col for _, col in points)
    return [values[left : right + 1] for values in grid[top : bottom + 1]]
