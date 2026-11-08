def solve(grid):
    repetitions = sum(value == 1 for value in grid[0])
    body = [(r, c) for r in range(1, len(grid))
            for c in range(len(grid[r])) if grid[r][c] != 0]
    top = min(r for r, c in body)
    bottom = max(r for r, c in body)
    left = min(c for r, c in body)
    right = max(c for r, c in body)
    height, width = bottom - top + 1, right - left + 1
    output = [[0] * (repetitions * width + repetitions - 1) for _ in range(height)]
    for copy_index in range(repetitions):
        offset = copy_index * (width + 1)
        for r in range(height):
            for c in range(width):
                output[r][offset + c] = grid[top + r][left + c]
    return output
