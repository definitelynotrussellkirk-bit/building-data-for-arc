def solve(grid):
    """Complete the colored frame and the gray cross through the red clue."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    colored = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    red = [(r, c) for r, c, value in colored if value == 2]
    frame_clues = [(r, c, value) for r, c, value in colored if value != 2]
    if not red or not frame_clues:
        return [row[:] for row in grid]

    top = min(r for r, _, _ in frame_clues)
    bottom = max(r for r, _, _ in frame_clues)
    left = min(c for _, c, _ in frame_clues)
    right = max(c for _, c, _ in frame_clues)

    top_color = next(value for r, _, value in frame_clues if r == top)
    bottom_color = next(value for r, _, value in frame_clues if r == bottom)
    left_color = next(value for _, c, value in frame_clues if c == left)
    right_color = next(value for _, c, value in frame_clues if c == right)

    red_row, red_col = red[0]

    # The red clue defines a full gray row and column within the frame.
    for c in range(left + 1, right):
        out[red_row][c] = 5
    for r in range(top + 1, bottom):
        out[r][red_col] = 5
    if top < red_row < bottom and left < red_col < right:
        out[red_row][red_col] = 2

    # Vertical sides are painted first; horizontal sides own all four corners.
    for r in range(top, bottom + 1):
        out[r][left] = left_color
        out[r][right] = right_color
    for c in range(left, right + 1):
        out[top][c] = top_color
        out[bottom][c] = bottom_color

    return out
