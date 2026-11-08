def solve(grid):
    """Extend the two interior seeds as a checkerboard inside their frame."""
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    colors = {value for row in grid for value in row if value != 0}
    frames = []
    for color in colors:
        cells = [(r, c) for r in range(height) for c in range(width)
                 if grid[r][c] == color]
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        if bottom - top < 2 or right - left < 2:
            continue
        border = {(r, c) for r in range(top, bottom + 1)
                  for c in range(left, right + 1)
                  if r in (top, bottom) or c in (left, right)}
        if set(cells) == border:
            frames.append((color, top, bottom, left, right))
    if len(frames) != 1:
        raise ValueError("Expected one complete rectangular frame")
    color, top, bottom, left, right = frames[0]
    phase = {}
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            value = grid[r][c]
            if value != 0:
                parity = (r + c) % 2
                if parity in phase and phase[parity] != value:
                    raise ValueError("Conflicting checkerboard seeds")
                phase[parity] = value
    if len(phase) != 2:
        raise ValueError("Expected a seed for each checkerboard parity")
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            out[r][c] = phase[(r + c) % 2]
    return out
