from collections import deque


def _normalize(cells):
    """Translate a finite cell set so its top-left bounding-box corner is (0, 0)."""
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _rotations(cells):
    """Return the four translation-normalized quarter-turns of a shape."""
    shape = set(cells)
    result = set()
    for _ in range(4):
        result.add(_normalize(shape))
        # A 90-degree turn; normalization removes the irrelevant negative offset.
        shape = {(c, -r) for r, c in shape}
    return result


def _components(grid, rows, allowed_colors):
    """Find 4-connected same-color components in the requested rows."""
    height = len(grid)
    width = len(grid[0])
    row_set = set(rows)
    seen = set()
    found = []

    for r in rows:
        for c in range(width):
            color = grid[r][c]
            if color not in allowed_colors or (r, c) in seen:
                continue

            queue = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while queue:
                cr, cc = queue.popleft()
                cells.add((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        nr in row_set
                        and 0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append((color, cells))

    return found


def solve(grid):
    """Recolor the lower object that is a rotation (not a reflection) of the clue."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]

    # The solid non-background row separates the blue clue from the candidates.
    separator = next(
        (
            r
            for r, row in enumerate(grid)
            if len(set(row)) == 1 and row[0] != 0
        ),
        None,
    )
    if separator is None:
        return out

    upper_rows = range(separator)
    lower_rows = range(separator + 1, height)

    upper_colors = {
        grid[r][c]
        for r in upper_rows
        for c in range(width)
        if grid[r][c] not in (0, grid[separator][0])
    }
    if not upper_colors:
        return out

    # The examples contain one clue color; taking all its cells also handles a
    # clue whose same-color pieces touch only diagonally.
    clue_color = min(upper_colors)
    clue = {
        (r, c)
        for r in upper_rows
        for c in range(width)
        if grid[r][c] == clue_color
    }
    target_shapes = _rotations(clue)

    candidate_colors = {
        grid[r][c]
        for r in lower_rows
        for c in range(width)
        if grid[r][c] not in (0, grid[separator][0], clue_color, 2)
    }
    for _, cells in _components(grid, lower_rows, candidate_colors):
        if _normalize(cells) in target_shapes:
            for r, c in cells:
                out[r][c] = 2
            break

    return out
