from collections import deque


def _seven_components(grid):
    """Return 4-connected components of the frame colour (7)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 7:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            yield component


def _is_rectangular_frame(grid, top, bottom, left, right):
    if bottom - top < 2 or right - left < 2:
        return False

    return (
        all(grid[top][col] == 7 and grid[bottom][col] == 7 for col in range(left, right + 1))
        and all(grid[row][left] == 7 and grid[row][right] == 7 for row in range(top, bottom + 1))
    )


def solve(grid):
    """
    In each 7-framed panel, use the panel's extra colour to fill every
    intersection between a row containing colour 2 and a column containing
    colour 3.  All row/column cues are read from the original input.
    """
    if not grid:
        return []
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be rectangular")

    result = [row[:] for row in grid]

    for component in _seven_components(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if not _is_rectangular_frame(grid, top, bottom, left, right):
            continue

        interior_rows = range(top + 1, bottom)
        interior_cols = range(left + 1, right)
        cue_rows = {
            row
            for row in interior_rows
            if any(grid[row][col] == 2 for col in interior_cols)
        }
        cue_cols = {
            col
            for col in interior_cols
            if any(grid[row][col] == 3 for row in interior_rows)
        }
        paint_colours = {
            grid[row][col]
            for row in interior_rows
            for col in interior_cols
            if grid[row][col] not in {0, 2, 3, 7}
        }

        # Every visible panel supplies exactly one paint-colour marker.
        if len(paint_colours) != 1:
            continue
        paint = next(iter(paint_colours))

        for row in cue_rows:
            for col in cue_cols:
                result[row][col] = paint

    return result
