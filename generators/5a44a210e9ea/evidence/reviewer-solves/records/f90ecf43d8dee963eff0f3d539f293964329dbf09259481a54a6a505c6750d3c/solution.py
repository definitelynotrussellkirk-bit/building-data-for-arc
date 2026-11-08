from collections import deque


def _components(grid, value):
    """Return 4-connected components containing ``value`` cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != value or (row, col) in seen:
                continue

            component = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                r, c = queue.popleft()
                component.add((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == value
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)

    return components


def _is_simple_cycle(component):
    """A finite 4-neighbour component is one simple cycle iff all degrees are 2."""
    if len(component) < 4:
        return False

    for row, col in component:
        degree = sum(
            (row + dr, col + dc) in component
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        if degree != 2:
            return False
    return True


def _cycle_order_key(component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    box_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    # The visible tasks contain nested cycles. Larger boxes are farther outside.
    return (-box_area, -len(component), min(rows), min(cols))


def solve(grid):
    """Recolor nested simple 1-cycles using the marker row's left-to-right palette."""
    if not grid:
        return []

    palette = [color for color in grid[0] if color != 0]
    body = [row[:] for row in grid[1:]]
    if not body:
        return []

    output = [[0 for _ in row] for row in body]
    cycles = [
        component
        for component in _components(body, 1)
        if _is_simple_cycle(component)
    ]
    cycles.sort(key=_cycle_order_key)

    if not palette:
        return output

    for index, component in enumerate(cycles):
        color = palette[min(index, len(palette) - 1)]
        for row, col in component:
            output[row][col] = color

    return output
