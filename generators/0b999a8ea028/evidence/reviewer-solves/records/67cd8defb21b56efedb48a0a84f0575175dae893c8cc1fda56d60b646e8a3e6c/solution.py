from collections import deque


def _components(grid, predicate):
    """Return 4-connected components whose cells satisfy predicate(value)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if (row, col) in seen or not predicate(grid[row][col]):
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                cur_row, cur_col = queue.popleft()
                component.append((cur_row, cur_col))
                for next_row, next_col in (
                    (cur_row - 1, cur_col),
                    (cur_row + 1, cur_col),
                    (cur_row, cur_col - 1),
                    (cur_row, cur_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if predicate(grid[next_row][next_col]):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            components.append(component)
    return components


def _rectangular_frame(component):
    """Return the component's bounds when it is exactly one hollow rectangle."""
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    if bottom - top + 1 < 3 or right - left + 1 < 3:
        return None

    border = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }
    return (top, bottom, left, right) if set(component) == border else None


def solve(grid):
    """Center the largest colored motif inside every intact isolated blue frame."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    if not grid or not grid[0]:
        return output

    motif_components = _components(grid, lambda value: value not in (0, 1))
    if not motif_components:
        return output

    motif = max(motif_components, key=len)
    motif_top = min(row for row, _ in motif)
    motif_bottom = max(row for row, _ in motif)
    motif_left = min(col for _, col in motif)
    motif_right = max(col for _, col in motif)
    motif_height = motif_bottom - motif_top + 1
    motif_width = motif_right - motif_left + 1
    normalized_motif = [
        (row - motif_top, col - motif_left, grid[row][col])
        for row, col in motif
    ]

    for component in _components(grid, lambda value: value == 1):
        bounds = _rectangular_frame(component)
        if bounds is None:
            continue
        top, bottom, left, right = bounds
        interior_height = bottom - top - 1
        interior_width = right - left - 1
        if motif_height > interior_height or motif_width > interior_width:
            continue

        target_top = top + 1 + (interior_height - motif_height) // 2
        target_left = left + 1 + (interior_width - motif_width) // 2
        for row_offset, col_offset, color in normalized_motif:
            output[target_top + row_offset][target_left + col_offset] = color

    return output
