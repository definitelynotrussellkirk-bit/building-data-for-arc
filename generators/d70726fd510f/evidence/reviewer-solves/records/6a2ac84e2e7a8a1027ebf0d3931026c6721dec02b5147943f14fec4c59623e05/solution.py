def solve(grid):
    """Overlay the panels and mark foreground exclusive-or in red."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    width = len(grid[0])
    if width % 2 != 1:
        raise ValueError("Expected two equal panels and one separator column")
    middle = width // 2
    if not all(row[middle] == 4 for row in grid):
        raise ValueError("Expected the visible yellow separator")
    return [
        [2 if bool(row[c]) != bool(row[middle + 1 + c]) else 0
         for c in range(middle)]
        for row in grid
    ]
