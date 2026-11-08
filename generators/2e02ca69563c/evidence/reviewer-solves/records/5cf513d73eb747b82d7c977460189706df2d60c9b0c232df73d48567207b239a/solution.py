from collections import Counter, deque


def _components(grid):
    """Yield four-connected nonzero monochrome components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield color, cells


def _frames(grid):
    """Return rectangular monochrome rings as (top, left, bottom, right, color)."""
    frames = []
    for color, cells in _components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if bottom - top < 2 or right - left < 2:
            continue
        perimeter = {
            (r, c)
            for r in range(top, bottom + 1)
            for c in range(left, right + 1)
            if r in (top, bottom) or c in (left, right)
        }
        if perimeter == set(cells):
            frames.append((top, left, bottom, right, color))
    return frames


def _paint_if_open(output, row, col, color):
    if output[row][col] in (0, color):
        output[row][col] = color


def solve(grid):
    """Connect every interior color that appears exactly twice in each frame.

    The two marks are joined by the demonstrated upper-row-first L: first across
    the upper endpoint's row to the lower endpoint's column, then vertically to
    the lower endpoint.  Existing differently colored marks are preserved.
    """
    output = [row[:] for row in grid]

    for top, left, bottom, right, frame_color in _frames(grid):
        positions = {}
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                color = grid[row][col]
                if color not in (0, frame_color):
                    positions.setdefault(color, []).append((row, col))

        for color, points in positions.items():
            if len(points) != 2:
                continue
            upper, lower = sorted(points)
            upper_row, upper_col = upper
            lower_row, lower_col = lower

            for col in range(min(upper_col, lower_col), max(upper_col, lower_col) + 1):
                _paint_if_open(output, upper_row, col, color)
            for row in range(min(upper_row, lower_row), max(upper_row, lower_row) + 1):
                _paint_if_open(output, row, lower_col, color)

    return output
