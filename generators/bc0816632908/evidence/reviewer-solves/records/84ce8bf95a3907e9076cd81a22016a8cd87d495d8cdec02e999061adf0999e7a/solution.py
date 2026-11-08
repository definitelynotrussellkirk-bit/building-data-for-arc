def solve(grid):
    """Recolor every third foreground component in left-to-right order."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 2 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)

    components.sort(key=lambda cells: min(col for _row, col in cells))
    output = [list(row) for row in grid]
    for index in range(0, len(components), 3):
        for row, col in components[index]:
            output[row][col] = 4
    return output
