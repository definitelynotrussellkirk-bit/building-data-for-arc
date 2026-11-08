def solve(grid):
    """Follow the visible script, retaining each cumulative template state."""
    points = [(r, c, value) for r, row in enumerate(grid) if r > 0
              for c, value in enumerate(row) if value != 0]
    top = min(r for r, _, _ in points)
    left = min(c for _, c, _ in points)
    points = [(r - top, c - left, value) for r, c, value in points]
    states = []
    for code in grid[0]:
        if code == 0:
            continue
        height = max(r for r, _, _ in points) + 1
        width = max(c for _, c, _ in points) + 1
        if code == 1:
            points = [(c, height - 1 - r, value) for r, c, value in points]
        elif code == 2:
            points = [(height - 1 - r, width - 1 - c, value) for r, c, value in points]
        elif code == 3:
            points = [(r, width - 1 - c, value) for r, c, value in points]
        elif code == 4:
            points = [(c, r, value) for r, c, value in points]
        else:
            raise ValueError("No visible interpretation established for this code")
        states.append(points)
    widths = [max(c for _, c, _ in state) + 1 for state in states]
    height = max(r for state in states for r, _, _ in state) + 1
    output = [[0] * (sum(widths) + len(states) - 1) for _ in range(height)]
    offset = 0
    for state, width in zip(states, widths):
        for r, c, value in state:
            output[r][offset + c] = value
        offset += width + 1
    return output
