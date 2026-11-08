from __future__ import annotations


def _largest_solid_rectangle(grid: list[list[int]], require_2d: bool):
    """Return (area, top, left, bottom, right, color) for the best rectangle."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    colors = sorted({value for row in grid for value in row if value != 0})

    best = None
    for color in colors:
        for top in range(height):
            valid_columns = [True] * width
            for bottom in range(top, height):
                for col in range(width):
                    valid_columns[col] = (
                        valid_columns[col] and grid[bottom][col] == color
                    )

                rect_height = bottom - top + 1
                run_start = None
                for col in range(width + 1):
                    is_valid = col < width and valid_columns[col]
                    if is_valid and run_start is None:
                        run_start = col
                    elif not is_valid and run_start is not None:
                        left = run_start
                        right = col - 1
                        rect_width = right - left + 1
                        run_start = None

                        if require_2d and (rect_height < 2 or rect_width < 2):
                            continue

                        candidate = (
                            rect_height * rect_width,
                            top,
                            left,
                            bottom,
                            right,
                            color,
                        )
                        if best is None or candidate[0] > best[0]:
                            best = candidate
    return best


def solve(grid):
    """Keep the largest solid nonzero rectangle and erase all other cells."""
    if not grid:
        return []
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be rectangular")

    best = _largest_solid_rectangle(grid, require_2d=True)
    if best is None:
        best = _largest_solid_rectangle(grid, require_2d=False)

    height = len(grid)
    width = len(grid[0])
    result = [[0 for _ in range(width)] for _ in range(height)]
    if best is None:
        return result

    _, top, left, bottom, right, color = best
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            result[row][col] = color
    return result
