"""Visible-example solver for the generated ARC lesson."""

from collections import deque


def _components8(grid):
    """Return nonzero 8-connected components in row-major discovery order."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                cur_row, cur_col = queue.popleft()
                component.append((cur_row, cur_col))
                for drow in (-1, 0, 1):
                    for dcol in (-1, 0, 1):
                        if drow == 0 and dcol == 0:
                            continue
                        nxt_row = cur_row + drow
                        nxt_col = cur_col + dcol
                        if not (0 <= nxt_row < height and 0 <= nxt_col < width):
                            continue
                        if grid[nxt_row][nxt_col] == 0:
                            continue
                        if (nxt_row, nxt_col) in seen:
                            continue
                        seen.add((nxt_row, nxt_col))
                        queue.append((nxt_row, nxt_col))

            components.append(component)

    return components


def _bbox(component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    return min(rows), min(cols), max(rows), max(cols)


def _sign(value):
    return (value > 0) - (value < 0)


def solve(grid):
    """
    Propagate the largest object's geometry along rays selected by the other
    colored fragments.

    A fragment's bounding-box center selects one of the eight directions (or
    a cardinal direction) relative to the largest object.  Copies are spaced
    by one blank row/column beyond that object's bounding-box dimensions and
    are painted with the fragment's color.  Existing nonzero cells win.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    components = _components8(grid)
    if not components:
        return [row[:] for row in grid]

    # Largest object is the reusable template.  Discovery order breaks an
    # otherwise unsupported tie deterministically.
    source_index = max(range(len(components)), key=lambda idx: len(components[idx]))
    source = components[source_index]
    source_top, source_left, source_bottom, source_right = _bbox(source)
    source_height = source_bottom - source_top + 1
    source_width = source_right - source_left + 1

    # Use doubled centers to avoid floating-point comparisons.
    source_center_row2 = source_top + source_bottom
    source_center_col2 = source_left + source_right

    source_offsets = [
        (row - source_top, col - source_left)
        for row, col in source
    ]

    output = [row[:] for row in grid]
    canvas_height = len(grid)
    canvas_width = len(grid[0])
    max_steps = max(canvas_height, canvas_width) + 1

    for index, marker in enumerate(components):
        if index == source_index:
            continue

        marker_top, marker_left, marker_bottom, marker_right = _bbox(marker)
        marker_center_row2 = marker_top + marker_bottom
        marker_center_col2 = marker_left + marker_right
        direction_row = _sign(marker_center_row2 - source_center_row2)
        direction_col = _sign(marker_center_col2 - source_center_col2)
        if direction_row == 0 and direction_col == 0:
            continue

        marker_color = grid[marker[0][0]][marker[0][1]]
        row_stride = source_height + 1
        col_stride = source_width + 1

        for step in range(1, max_steps + 1):
            copy_top = source_top + step * direction_row * row_stride
            copy_left = source_left + step * direction_col * col_stride

            # Once a monotone ray's entire source bounding box is beyond the
            # canvas, all later copies are beyond it as well.
            if direction_row < 0 and copy_top + source_height - 1 < 0:
                break
            if direction_row > 0 and copy_top >= canvas_height:
                break
            if direction_col < 0 and copy_left + source_width - 1 < 0:
                break
            if direction_col > 0 and copy_left >= canvas_width:
                break

            for offset_row, offset_col in source_offsets:
                target_row = copy_top + offset_row
                target_col = copy_left + offset_col
                if not (0 <= target_row < canvas_height and 0 <= target_col < canvas_width):
                    continue
                if output[target_row][target_col] == 0:
                    output[target_row][target_col] = marker_color

    return output
