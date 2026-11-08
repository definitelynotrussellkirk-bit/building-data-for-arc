def solve(grid):
    """Transfer the demonstrated hollowing operation to the lower-left object."""
    result = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    separators = []
    for row in range(1, height - 1):
        color = grid[row][0]
        if color == 0 or any(cell != color for cell in grid[row]):
            continue
        for col in range(1, width - 1):
            if all(grid[r][col] == color for r in range(height)):
                separators.append((row, col, color))
    if len(separators) != 1:
        raise ValueError("Expected one full horizontal and vertical separator")
    split_row, split_col, separator_color = separators[0]
    occupied = [(r, c) for r in range(split_row + 1, height)
                for c in range(split_col)
                if grid[r][c] not in (0, separator_color)]
    if not occupied:
        return result
    first_row, first_col = occupied[0]
    color = grid[first_row][first_col]
    top, bottom = min(r for r, _ in occupied), max(r for r, _ in occupied)
    left, right = min(c for _, c in occupied), max(c for _, c in occupied)
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            target_col = split_col + 1 + c
            if target_col >= width:
                continue
            is_edge = r in (top, bottom) or c in (left, right)
            result[r][target_col] = color if is_edge and grid[r][c] != 0 else 0
    return result
