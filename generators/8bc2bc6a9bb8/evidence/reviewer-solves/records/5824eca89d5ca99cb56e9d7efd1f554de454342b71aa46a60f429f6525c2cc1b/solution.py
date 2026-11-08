from collections import deque


def _components_of_eight(grid):
    """Return 4-connected components made of color 8 below the key row."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(1, height):
        for col in range(width):
            if grid[row][col] != 8 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []

            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (1 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 8:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            components.append(component)

    return components


def solve(grid):
    """Recolor size-ranked gray objects and pack them along a common baseline."""
    if not grid or not grid[0]:
        return []

    key_colors = [value for value in grid[0] if value not in (0, 8)]
    components = _components_of_eight(grid)

    # The examples use distinct component sizes.  The coordinate tie-breakers keep
    # behavior deterministic without changing the observed size-ranking rule.
    components.sort(
        key=lambda component: (
            -len(component),
            min(row for row, _ in component),
            min(col for _, col in component),
        )
    )

    if len(key_colors) != len(components):
        raise ValueError("the top-row key must contain one color per gray component")

    normalized = []
    for component, color in zip(components, key_colors):
        min_row = min(row for row, _ in component)
        max_row = max(row for row, _ in component)
        min_col = min(col for _, col in component)
        max_col = max(col for _, col in component)
        cells = {(row - min_row, col - min_col) for row, col in component}
        normalized.append((cells, max_row - min_row + 1, max_col - min_col + 1, color))

    output_height = max((item_height for _, item_height, _, _ in normalized), default=0)
    output_width = sum(item_width for _, _, item_width, _ in normalized)
    if normalized:
        output_width += len(normalized) - 1

    output = [[0 for _ in range(output_width)] for _ in range(output_height)]
    left = 0
    for cells, item_height, item_width, color in normalized:
        top = output_height - item_height
        for row, col in cells:
            output[top + row][left + col] = color
        left += item_width + 1

    return output
