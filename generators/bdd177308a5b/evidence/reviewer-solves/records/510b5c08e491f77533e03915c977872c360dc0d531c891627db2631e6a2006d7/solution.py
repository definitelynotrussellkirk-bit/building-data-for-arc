"""Infer matching objects from the visible gray-framed shape."""


def _normalized(cells):
    top = min(row for row, col in cells)
    left = min(col for row, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def solve(grid):
    """Recolor translated copies of the framed template with gray (5)."""
    output = [list(row) for row in grid]
    if not grid or not grid[0]:
        return output

    height, width = len(grid), len(grid[0])
    gray = [(row, col) for row in range(height) for col in range(width)
            if grid[row][col] == 5]
    if not gray:
        return output

    top = min(row for row, col in gray)
    bottom = max(row for row, col in gray)
    left = min(col for row, col in gray)
    right = max(col for row, col in gray)
    template = {(row, col) for row in range(top, bottom)
                for col in range(left, right) if grid[row][col] not in (0, 5)}
    if not template:
        return output
    template_shape = _normalized(template)

    # Keep colors separate: different objects can touch in a query.
    visited = set()
    for row in range(height):
        for col in range(width):
            start = (row, col)
            color = grid[row][col]
            if color in (0, 5) or start in visited:
                continue
            component = {start}
            visited.add(start)
            pending = [start]
            while pending:
                r, c = pending.pop()
                for nr, nc in ((r - 1, c), (r + 1, c),
                               (r, c - 1), (r, c + 1)):
                    point = (nr, nc)
                    if (0 <= nr < height and 0 <= nc < width
                            and point not in visited and grid[nr][nc] == color):
                        visited.add(point)
                        component.add(point)
                        pending.append(point)
            if component.isdisjoint(template) and _normalized(component) == template_shape:
                for r, c in component:
                    output[r][c] = 5
    return output
