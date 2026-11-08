from collections import deque


def _components(grid):
    """Return 4-connected components of non-background cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 0 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append(cells)

    return components


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    if height == 0 or width == 0:
        return [row[:] for row in grid]

    components = _components(grid)
    if not components:
        return [row[:] for row in grid]

    # The prototype is the only connected object that contains several colors.
    prototype = max(
        components,
        key=lambda cells: (len({grid[row][col] for row, col in cells}), len(cells)),
    )
    prototype_set = set(prototype)

    positions_by_color = {}
    prototype_positions_by_color = {}
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            positions_by_color.setdefault(color, []).append((row, col))
            if (row, col) in prototype_set:
                prototype_positions_by_color.setdefault(color, []).append((row, col))

    # Two singleton colors decorate the prototype.  The one repeated elsewhere
    # is the anchor at which the whole prototype is stamped.
    singleton_colors = [
        color
        for color, positions in prototype_positions_by_color.items()
        if len(positions) == 1
    ]
    if not singleton_colors:
        return [row[:] for row in grid]

    anchor_color = max(
        singleton_colors,
        key=lambda color: (
            len(positions_by_color.get(color, ())) - 1,
            len(positions_by_color.get(color, ())),
        ),
    )
    anchor_row, anchor_col = prototype_positions_by_color[anchor_color][0]

    stamp = [
        (row - anchor_row, col - anchor_col, grid[row][col])
        for row, col in prototype
    ]
    output = [[0 for _ in range(width)] for _ in range(height)]

    for target_row, target_col in positions_by_color[anchor_color]:
        for delta_row, delta_col, color in stamp:
            row = target_row + delta_row
            col = target_col + delta_col
            if not (0 <= row < height and 0 <= col < width):
                continue
            previous = output[row][col]
            if previous == 0 or previous == color:
                output[row][col] = color
            elif previous != 9:
                output[row][col] = 9

    return output
