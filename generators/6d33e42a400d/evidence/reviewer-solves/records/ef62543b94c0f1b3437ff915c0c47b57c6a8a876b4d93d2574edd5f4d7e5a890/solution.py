from collections import Counter


def solve(grid):
    """Reflect the terrain profile from the sparse marker line to its twin."""
    if not grid or not grid[0]:
        return grid
    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    foreground = [value for value in counts if value != background]
    if len(foreground) != 2:
        raise ValueError("expected background plus source and marker colors")
    source = max(foreground, key=lambda value: counts[value])
    paint = next(value for value in foreground if value != source)

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == paint
    ]
    source_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == source
    ]
    output = [row[:] for row in grid]

    if len({row for row, _ in markers}) == 1:
        marker_line = markers[0][0]
        marker_coords = sorted(col for _, col in markers)
        candidates = []
        for row in range(height):
            if row == marker_line:
                continue
            coords = sorted(col for r, col in source_cells if r == row)
            if coords == marker_coords:
                candidates.append(row)
        if len(candidates) != 1:
            raise ValueError("could not identify the parallel source marker row")
        target_line = candidates[0]
        terrain_side = -1 if target_line > marker_line else 1
        for row, col in source_cells:
            side = -1 if row < marker_line else 1 if row > marker_line else 0
            if side != terrain_side:
                continue
            new_row = target_line + marker_line - row
            if 0 <= new_row < height:
                output[new_row][col] = paint
    elif len({col for _, col in markers}) == 1:
        marker_line = markers[0][1]
        marker_coords = sorted(row for row, _ in markers)
        candidates = []
        for col in range(width):
            if col == marker_line:
                continue
            coords = sorted(row for row, c in source_cells if c == col)
            if coords == marker_coords:
                candidates.append(col)
        if len(candidates) != 1:
            raise ValueError("could not identify the parallel source marker column")
        target_line = candidates[0]
        terrain_side = -1 if target_line > marker_line else 1
        for row, col in source_cells:
            side = -1 if col < marker_line else 1 if col > marker_line else 0
            if side != terrain_side:
                continue
            new_col = target_line + marker_line - col
            if 0 <= new_col < width:
                output[row][new_col] = paint
    else:
        raise ValueError("marker color must form one sparse row or column")

    return output
