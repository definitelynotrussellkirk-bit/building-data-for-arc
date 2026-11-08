def solve(grid):
    """Return the leftmost of three equally wide horizontal panels."""
    if not grid:
        return []
    width = len(grid[0])
    if width % 3 != 0 or any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid with width divisible by 3")
    panel_width = width // 3
    return [row[:panel_width] for row in grid]
