from collections import deque


def _largest_left_component(left):
    """Return (color, normalized_cells, height, width) for the largest 4-component."""
    height = len(left)
    width = len(left[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = left[row][col]
            if color == 0 or (row, col) in seen:
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
                    if (next_row, next_col) in seen:
                        continue
                    if left[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append((len(cells), color, cells))

    if not components:
        return None

    # A smaller disconnected left-hand object can be a distractor; the examples
    # consistently use the largest connected object as the completion template.
    _, color, cells = max(components, key=lambda item: (item[0], -min(r for r, _ in item[2]), -min(c for _, c in item[2])))
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    normalized = {(row - min_row, col - min_col) for row, col in cells}
    template_height = max(row for row, _ in normalized) + 1
    template_width = max(col for _, col in normalized) + 1
    return color, normalized, template_height, template_width


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0

    divider_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    if not divider_columns:
        return [row[:] for row in grid]

    divider = divider_columns[0]
    left = [row[:divider] for row in grid]
    result = [row[divider + 1 :] for row in grid]

    template = _largest_left_component(left)
    if template is None:
        return result

    color, support, template_height, template_width = template
    result_width = len(result[0]) if result else 0
    additions = set()

    # Match translated copies in the original right panel. A valid near-copy has
    # every template cell except one, no same-colored extras inside the bounding
    # box, and an empty cell at the one missing location.
    for top in range(height - template_height + 1):
        for left_col in range(result_width - template_width + 1):
            missing = []
            valid = True
            for local_row in range(template_height):
                for local_col in range(template_width):
                    value = result[top + local_row][left_col + local_col]
                    if (local_row, local_col) in support:
                        if value == color:
                            continue
                        if value == 0:
                            missing.append((top + local_row, left_col + local_col))
                            if len(missing) > 1:
                                valid = False
                                break
                        else:
                            valid = False
                            break
                    elif value == color:
                        valid = False
                        break
                if not valid:
                    break
            if valid and len(missing) == 1:
                additions.add(missing[0])

    for row, col in additions:
        result[row][col] = color
    return result
