from collections import deque


def _yellow_components(grid):
    """Return 4-connected components made from ARC yellow (colour 4)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 4 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 4:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            yield component


def solve(grid):
    """
    Fill each hollow yellow rectangle with the colour of its interior marker.

    Cells outside the rectangles, the yellow borders, and the marker itself are
    preserved.  The examples contain one non-zero, non-yellow marker inside
    every yellow frame.
    """
    output = [row[:] for row in grid]

    for component in _yellow_components(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)

        # A relevant yellow object is a closed rectangular border.  This guard
        # prevents an unrelated yellow fragment from defining a fill region.
        if bottom - top < 2 or right - left < 2:
            continue
        border = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
            if row in (top, bottom) or col in (left, right)
        }
        if not border.issubset(set(component)):
            continue

        markers = [
            grid[row][col]
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
            if grid[row][col] not in (0, 4)
        ]
        if not markers:
            continue
        marker_colour = markers[0]

        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                if grid[row][col] == 0:
                    output[row][col] = marker_colour

    return output
