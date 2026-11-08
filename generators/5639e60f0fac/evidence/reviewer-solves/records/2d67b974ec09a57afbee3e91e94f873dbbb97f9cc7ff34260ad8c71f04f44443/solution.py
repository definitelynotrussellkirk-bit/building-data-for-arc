"""Visible-example hypothesis: transfer the green binary crop to the cyan block."""

def solve(grid):
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not green or not cyan:
        raise ValueError('need a green pattern and a cyan canvas')
    top = min(r for r, c in green)
    left = min(c for r, c in green)
    height = max(r for r, c in green) - top + 1
    width = max(c for r, c in green) - left + 1
    target_top = min(r for r, c in cyan)
    target_left = min(c for r, c in cyan)
    target_shape = (max(r for r, c in cyan) - target_top + 1,
                    max(c for r, c in cyan) - target_left + 1)
    if target_shape != (height, width) or len(cyan) != height * width:
        raise ValueError('cyan canvas must be solid and match the green crop')
    answer = [row[:] for row in grid]
    for dr in range(height):
        for dc in range(width):
            answer[target_top + dr][target_left + dc] = 8 if grid[top + dr][left + dc] == 3 else 0
    return answer
