def solve(grid):
    """Overlay the three width-4 panels and keep cells occupied in >=2 panels."""
    if not grid or any(len(row) != 14 for row in grid):
        raise ValueError("expected a nonempty 14-column grid")
    panel_starts = (0, 5, 10)
    return [
        [
            8
            if sum(grid[row][start + col] != 0 for start in panel_starts) >= 2
            else 0
            for col in range(4)
        ]
        for row in range(len(grid))
    ]
