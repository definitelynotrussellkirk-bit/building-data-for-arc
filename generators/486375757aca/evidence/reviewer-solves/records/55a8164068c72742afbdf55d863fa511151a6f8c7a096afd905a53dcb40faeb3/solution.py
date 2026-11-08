"""Visible-example solution for blind task 486375757aca.

The input contains blue (1) rectangular frames.  Each frame contains one
non-background, non-blue marker.  A frame's interior is filled with its marker
colour.  When two frame borders touch orthogonally, the later frame in
row-major order also paints the inclusive rectangle between the two markers;
this bridge is applied after the ordinary interior fills.
"""


def _boundary_is_blue(grid, top, bottom, left, right):
    return (
        all(grid[top][c] == 1 and grid[bottom][c] == 1
            for c in range(left, right + 1))
        and all(grid[r][left] == 1 and grid[r][right] == 1
                for r in range(top, bottom + 1))
    )


def _smallest_frame_around(grid, marker_row, marker_col):
    """Return the smallest all-blue rectangular frame enclosing a marker."""
    height, width = len(grid), len(grid[0])
    candidates = []
    for top in range(marker_row):
        for bottom in range(marker_row + 1, height):
            for left in range(marker_col):
                for right in range(marker_col + 1, width):
                    if _boundary_is_blue(grid, top, bottom, left, right):
                        area = (bottom - top + 1) * (right - left + 1)
                        candidates.append((area, top, left, bottom, right))
    if not candidates:
        return None
    _, top, left, bottom, right = min(candidates)
    return top, bottom, left, right


def _border_cells(frame):
    top, bottom, left, right = frame
    cells = {(top, c) for c in range(left, right + 1)}
    cells.update((bottom, c) for c in range(left, right + 1))
    cells.update((r, left) for r in range(top, bottom + 1))
    cells.update((r, right) for r in range(top, bottom + 1))
    return cells


def _touch_orthogonally(frame_a, frame_b):
    border_b = _border_cells(frame_b)
    for row, col in _border_cells(frame_a):
        if ((row - 1, col) in border_b or (row + 1, col) in border_b
                or (row, col - 1) in border_b
                or (row, col + 1) in border_b):
            return True
    return False


def solve(grid):
    output = [row[:] for row in grid]

    markers = []
    for row, values in enumerate(grid):
        for col, colour in enumerate(values):
            if colour not in (0, 1):
                frame = _smallest_frame_around(grid, row, col)
                if frame is not None:
                    top, bottom, left, right = frame
                    markers.append({
                        "row": row,
                        "col": col,
                        "colour": colour,
                        "frame": frame,
                        "order": (top, left, bottom, right),
                    })

    # First perform the independent frame fills.
    for marker in markers:
        top, bottom, left, right = marker["frame"]
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                output[row][col] = marker["colour"]

    # Then apply interactions in row-major frame order, so a later/lower frame
    # supplies the colour where two touching-frame bridges overlap.
    markers.sort(key=lambda item: item["order"])
    for later_index, later in enumerate(markers):
        for earlier in markers[:later_index]:
            if not _touch_orthogonally(earlier["frame"], later["frame"]):
                continue
            row0, row1 = sorted((earlier["row"], later["row"]))
            col0, col1 = sorted((earlier["col"], later["col"]))
            for row in range(row0, row1 + 1):
                for col in range(col0, col1 + 1):
                    output[row][col] = later["colour"]

    return output
