"""Standalone attempted solution from this episode's visible examples."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width or any(len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    markers = {color: [(r, c) for r, row in enumerate(grid)
                       for c, value in enumerate(row) if value == color]
               for color in (9, 7)}
    if any(not cells for cells in markers.values()):
        raise ValueError("both marker colors are required")
    bounds = {}
    for color, cells in markers.items():
        rows, cols = zip(*cells)
        bounds[color] = (min(rows), min(cols), max(rows), max(cols))
    result = [[7 if value == 9 else 6 if value == 7 else value for value in row]
              for row in grid]
    top9, left9, bottom9, right9 = bounds[9]
    top7, left7, bottom7, right7 = bounds[7]
    if left9 == left7:
        for r in range(min(bottom9, bottom7) + 1, max(top9, top7)):
            if 0 in grid[r]:
                for c in range(left9, right9 + 1):
                    if grid[r][c] == 6:
                        result[r][c] = 2
    else:
        # Symmetric extrapolation; this visible episode only tests vertical scenes.
        for c in range(min(right9, right7) + 1, max(left9, left7)):
            if any(grid[r][c] == 0 for r in range(height)):
                for r in range(top9, bottom9 + 1):
                    if grid[r][c] == 6:
                        result[r][c] = 2
    return result
