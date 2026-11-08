"""Visible-only solution for the assigned ARC puzzle."""

from collections import deque


def _nine_frames(grid):
    """Return rectangular 9-borders as (top, left, bottom, right)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    frames = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 9 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = set()
            while queue:
                current_row, current_col = queue.popleft()
                component.add((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == 9
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))

            top = min(position[0] for position in component)
            bottom = max(position[0] for position in component)
            left = min(position[1] for position in component)
            right = max(position[1] for position in component)
            if bottom - top < 2 or right - left < 2:
                continue

            border = {
                (border_row, border_col)
                for border_row in range(top, bottom + 1)
                for border_col in range(left, right + 1)
                if border_row in (top, bottom) or border_col in (left, right)
            }
            if component == border:
                frames.append((top, left, bottom, right))

    return sorted(frames)


def solve(grid):
    """Encode which legend colors occur inside each framed panel."""
    frames = _nine_frames(grid)
    if not frames:
        return []

    # The colored legend is placed before the framed panels.  Read its colors
    # left-to-right (and top-to-bottom if it ever spans more than one row).
    first_frame_row = min(frame[0] for frame in frames)
    legend = []
    for row in range(first_frame_row):
        for value in grid[row]:
            if value not in (0, 9) and value not in legend:
                legend.append(value)

    # Defensive fallback for a layout with no blank row above the frames.
    if not legend:
        for row, values in enumerate(grid):
            for col, value in enumerate(values):
                inside_frame = any(
                    top <= row <= bottom and left <= col <= right
                    for top, left, bottom, right in frames
                )
                if not inside_frame and value not in (0, 9) and value not in legend:
                    legend.append(value)

    output = []
    for top, left, bottom, right in frames:
        interior_colors = {
            grid[row][col]
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
        }
        output.append([color if color in interior_colors else 0 for color in legend])
    return output
