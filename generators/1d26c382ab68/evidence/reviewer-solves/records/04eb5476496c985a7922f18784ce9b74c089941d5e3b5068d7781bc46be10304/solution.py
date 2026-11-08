from collections import deque


def _normalize(points):
    """Translate a finite cell set so its top-left bounding-box corner is (0, 0)."""
    points = tuple(points)
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return frozenset((r - min_r, c - min_c) for r, c in points)


def _rotations(points):
    """Return the distinct normalized quarter-turn rotations of a cell set."""
    current = _normalize(points)
    result = set()
    for _ in range(4):
        result.add(current)
        # Rotating (row, col) to (col, -row) is a 90-degree quarter turn;
        # normalization removes the temporary negative translation.
        current = _normalize((c, -r) for r, c in current)
    return result


def _components(grid, start_row):
    """Yield 4-connected, same-color components strictly below start_row."""
    height = len(grid)
    width = len(grid[0])
    seen = set()

    for r in range(start_row, height):
        for c in range(width):
            color = grid[r][c]
            if color in (0, 1, 2, 9) or (r, c) in seen:
                continue

            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        start_row <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield color, cells


def solve(grid):
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    divider_rows = [r for r, row in enumerate(grid) if row and all(value == 9 for value in row)]
    if not divider_rows:
        return [row[:] for row in grid]
    divider = divider_rows[0]

    template = [(r, c) for r in range(divider) for c, value in enumerate(grid[r]) if value == 1]
    if not template:
        return [row[:] for row in grid]
    target_rotations = _rotations(template)

    result = [row[:] for row in grid]
    for _color, cells in _components(grid, divider + 1):
        if _normalize(cells) in target_rotations:
            for r, c in cells:
                result[r][c] = 2
    return result
