from collections import Counter, deque


def _components(grid, background):
    """Return 4-connected components of all non-background cells."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue

            queue = [(row, col)]
            seen.add((row, col))
            component = []
            for current_row, current_col in queue:
                component.append((current_row, current_col))
                for row_delta, col_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + row_delta
                    next_col = current_col + col_delta
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == background:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            components.append(component)

    return components


def _is_closed(mask):
    """A solid shape or a shape enclosing a background cell is closed."""
    height = len(mask)
    width = len(mask[0])

    if all(all(row) for row in mask):
        return True

    # Flood the empty cells in a one-cell frame around the bounding box. Any
    # empty cell not reached by this exterior flood is an enclosed hole.
    framed_height = height + 2
    framed_width = width + 2
    occupied = [[False] * framed_width for _ in range(framed_height)]
    for row in range(height):
        for col in range(width):
            occupied[row + 1][col + 1] = mask[row][col]

    exterior = {(0, 0)}
    queue = deque([(0, 0)])
    while queue:
        row, col = queue.popleft()
        for row_delta, col_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            next_row = row + row_delta
            next_col = col + col_delta
            if not (0 <= next_row < framed_height and 0 <= next_col < framed_width):
                continue
            if occupied[next_row][next_col] or (next_row, next_col) in exterior:
                continue
            exterior.add((next_row, next_col))
            queue.append((next_row, next_col))

    return any(
        not mask[row][col] and (row + 1, col + 1) not in exterior
        for row in range(height)
        for col in range(width)
    )


def solve(grid):
    """Move closed objects to the left in blue and open objects right in green."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    output = [[background] * width for _ in range(height)]

    for component in _components(grid, background):
        top = min(row for row, _ in component)
        bottom = max(row for row, _ in component)
        left = min(col for _, col in component)
        right = max(col for _, col in component)
        object_height = bottom - top + 1
        object_width = right - left + 1

        mask = [[False] * object_width for _ in range(object_height)]
        for row, col in component:
            mask[row - top][col - left] = True

        closed = _is_closed(mask)
        target_left = 0 if closed else width - object_width
        target_color = 2 if closed else 3

        for row in range(object_height):
            for col in range(object_width):
                if mask[row][col]:
                    output[top + row][target_left + col] = target_color

    return output
