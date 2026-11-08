def solve(grid):
    """Invert the interiors of the frames, preserving left-to-right order."""
    height, width = len(grid), len(grid[0])
    occupied = [any(grid[r][c] != 0 for r in range(height)) for c in range(width)]
    groups = []
    column = 0
    while column < width:
        if not occupied[column]:
            column += 1
            continue
        left = column
        while column < width and occupied[column]:
            column += 1
        right = column - 1
        cells = [(r, c) for r in range(height) for c in range(left, right + 1)
                 if grid[r][c] != 0]
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        color = max({grid[r][c] for r, c in cells},
                    key=lambda value: sum(grid[r][c] == value for r, c in cells))
        interior = [[color if grid[r][c] == 0 else 0
                     for c in range(left + 1, right)]
                    for r in range(top + 1, bottom)]
        groups.append(interior)
    output_height = max(len(part) for part in groups)
    output = [[] for _ in range(output_height)]
    for index, part in enumerate(groups):
        part_width = len(part[0]) if part else 0
        for row in range(output_height):
            if index:
                output[row].append(0)
            output[row].extend(part[row] if row < len(part) else [0] * part_width)
    return output
