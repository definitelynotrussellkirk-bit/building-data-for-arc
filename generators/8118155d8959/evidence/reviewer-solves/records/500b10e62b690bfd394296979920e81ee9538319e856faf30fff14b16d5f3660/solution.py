def solve(grid):
    """Recolor the three 4-connected gray objects by increasing area.

    Smallest -> red (2), middle -> green (3), largest -> azure (8).
    All other cells are preserved.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)

    if len(components) != 3:
        raise ValueError(f"expected three gray objects, found {len(components)}")

    components.sort(key=lambda cells: (len(cells), min(cells)))
    for component, color in zip(components, (2, 3, 8)):
        for row, col in component:
            output[row][col] = color
    return output
