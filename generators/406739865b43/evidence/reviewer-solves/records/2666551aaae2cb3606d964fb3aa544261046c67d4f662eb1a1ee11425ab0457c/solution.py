from collections import defaultdict, deque


def solve(grid):
    """Extract the non-singleton component whose color also marks itself by a singleton."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components_by_color = defaultdict(list)

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            components_by_color[color].append(component)

    candidates = []
    for color, components in components_by_color.items():
        if any(len(component) == 1 for component in components):
            larger = [component for component in components if len(component) > 1]
            if larger:
                marker_row = min(
                    row
                    for component in components
                    if len(component) == 1
                    for row, _ in component
                )
                candidates.append((marker_row, color, max(larger, key=len)))

    if not candidates:
        return []

    _, color, component = min(candidates, key=lambda item: (item[0], item[1]))
    min_row = min(row for row, _ in component)
    max_row = max(row for row, _ in component)
    min_col = min(col for _, col in component)
    max_col = max(col for _, col in component)
    cells = set(component)

    return [
        [color if (row, col) in cells else 0 for col in range(min_col, max_col + 1)]
        for row in range(min_row, max_row + 1)
    ]
