from collections import deque


def _components(grid, excluded=(0, 5)):
    """Return 4-connected monochrome components not using excluded colors."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color in excluded or (row, col) in seen:
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
            result.append((color, cells))
    return result


def _shape(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def solve(grid):
    output = [row[:] for row in grid]
    if not grid or not grid[0]:
        return output

    # The color-5 divider is an L. Its longest row and column meet at the
    # lower-right corner of the template compartment.
    divider_row = max(range(len(grid)), key=lambda r: sum(v == 5 for v in grid[r]))
    divider_col = max(
        range(len(grid[0])),
        key=lambda c: sum(grid[r][c] == 5 for r in range(len(grid))),
    )

    components = _components(grid)
    templates = [
        cells
        for _, cells in components
        if all(row < divider_row and col < divider_col for row, col in cells)
    ]
    if not templates:
        return output

    # The visible task has one template; selecting the largest makes the intent
    # stable if isolated noise is ever present in the compartment.
    template_cells = max(templates, key=len)
    template_shape = _shape(template_cells)
    template_set = set(template_cells)

    for _, cells in components:
        if set(cells) == template_set:
            continue
        if _shape(cells) == template_shape:
            for row, col in cells:
                output[row][col] = 5

    return output
