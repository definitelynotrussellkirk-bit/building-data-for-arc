from collections import deque


RANK_COLORS = (2, 4, 6, 7)


def _components(grid, color=8):
    height = len(grid)
    width = len(grid[0]) if height else 0
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + delta_row, col + delta_col)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        result.append(cells)
    return result


def _bbox_area(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def solve(grid):
    """Recolor each color-8 object by descending bounding-box size.

    The largest object becomes 2, the next 4, then 6, then 7.  Nested
    rectangles remain separate 4-connected objects because a zero moat lies
    between them, so the same size ranking handles both nested and disjoint
    examples.
    """
    output = [row[:] for row in grid]
    components = _components(grid, 8)
    components.sort(
        key=lambda cells: (
            -_bbox_area(cells),
            min(row for row, _ in cells),
            min(col for _, col in cells),
        )
    )

    for index, cells in enumerate(components):
        if index >= len(RANK_COLORS):
            break
        replacement = RANK_COLORS[index]
        for row, col in cells:
            output[row][col] = replacement
    return output
