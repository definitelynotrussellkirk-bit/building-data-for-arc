def _split_on_full_color_columns(grid, color=9):
    """Split a rectangular grid at columns filled entirely with ``color``."""
    height = len(grid)
    width = len(grid[0])
    separators = {
        c for c in range(width) if all(grid[r][c] == color for r in range(height))
    }

    blocks = []
    start = 0
    for c in range(width + 1):
        if c == width or c in separators:
            if start < c:
                blocks.append([row[start:c] for row in grid])
            start = c + 1
    return blocks


def _only_nonzero_color(block):
    colors = {value for row in block for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"expected one foreground color, found {sorted(colors)}")
    return next(iter(colors))


def _normalized_cells(block, color):
    cells = [
        (r, c)
        for r, row in enumerate(block)
        for c, value in enumerate(row)
        if value == color
    ]
    if not cells:
        return frozenset()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _crop_four_rows(block):
    foreground_rows = [
        r for r, row in enumerate(block) if any(value != 0 for value in row)
    ]
    if not foreground_rows:
        raise ValueError("candidate block is empty")

    first = min(foreground_rows)
    last = max(foreground_rows)
    if last - first + 1 > 4:
        raise ValueError("candidate foreground is taller than four rows")

    # The authored candidates span four rows in the visible lesson.  The
    # clamping keeps the extraction well-defined if a border row is blank.
    start = min(first, len(block) - 4)
    start = max(0, start)
    if last >= start + 4:
        start = last - 3
    return [row[:] for row in block[start : start + 4]]


def solve(grid):
    blocks = _split_on_full_color_columns(grid)
    if len(blocks) != 5 or [len(b[0]) for b in blocks[:4]] != [3, 4, 3, 4]:
        raise ValueError("unexpected panel layout")

    clue = blocks[4]
    matches = []
    for marker_index, candidate_index in ((0, 1), (2, 3)):
        marker = blocks[marker_index]
        marker_color = _only_nonzero_color(marker)
        marker_shape = _normalized_cells(marker, marker_color)
        clue_shape = _normalized_cells(clue, marker_color)
        if marker_shape == clue_shape:
            matches.append(candidate_index)

    if len(matches) != 1:
        raise ValueError(f"expected exactly one reproduced key, found {len(matches)}")
    return _crop_four_rows(blocks[matches[0]])
