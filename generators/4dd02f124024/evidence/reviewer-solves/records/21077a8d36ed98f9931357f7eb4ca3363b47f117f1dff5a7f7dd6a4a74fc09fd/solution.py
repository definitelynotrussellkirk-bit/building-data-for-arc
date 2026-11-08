from collections import Counter, deque


def _components(grid, color):
    rows, cols = len(grid), len(grid[0])
    seen = set()
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            yield cells


def _framed_boxes(grid, excluded_color=None):
    """Return complete monochrome rectangular frames as (color, bounds)."""
    colors = {value for row in grid for value in row if value != 0}
    boxes = []
    for color in colors:
        if color == excluded_color:
            continue
        for cells in _components(grid, color):
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            top, bottom = min(rs), max(rs)
            left, right = min(cs), max(cs)
            if bottom - top < 2 or right - left < 2:
                continue
            perimeter = (
                {(top, c) for c in range(left, right + 1)}
                | {(bottom, c) for c in range(left, right + 1)}
                | {(r, left) for r in range(top, bottom + 1)}
                | {(r, right) for r in range(top, bottom + 1)}
            )
            if all(grid[r][c] == color for r, c in perimeter):
                boxes.append((color, top, bottom, left, right))
    return boxes


def solve(grid):
    """Clean the interiors of every rectangular frame carrying rare marker pixels."""
    out = [row[:] for row in grid]
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return out

    # The marker is the non-background color whose pixels sit inside other
    # colors' complete frames.  Frequency breaks ties and covers degenerate cases.
    best = None
    for candidate, count in counts.items():
        boxes = _framed_boxes(grid, excluded_color=candidate)
        points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == candidate]
        contained = sum(
            any(top < r < bottom and left < c < right for _, top, bottom, left, right in boxes)
            for r, c in points
        )
        score = (contained == len(points), contained, -count)
        if best is None or score > best[0]:
            best = (score, candidate)
    marker = best[1]
    marker_points = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == marker
    }

    # A marked frame is repaired to a clean hollow rectangle.  Unmarked
    # irregular frames/objects are distractors and remain untouched.
    for _, top, bottom, left, right in _framed_boxes(grid, excluded_color=marker):
        if any(top < r < bottom and left < c < right for r, c in marker_points):
            for r in range(top + 1, bottom):
                for c in range(left + 1, right):
                    out[r][c] = 0

    # Defensive cleanup for any marker pixel not covered by a recognized frame.
    for r, c in marker_points:
        out[r][c] = 0
    return out
