from collections import Counter, deque


def _components(grid, color):
    height, width = len(grid), len(grid[0])
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
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + dr, col + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def solve(grid):
    height, width = len(grid), len(grid[0])
    counts = Counter(cell for row in grid for cell in row)
    background = min(counts, key=lambda color: (-counts[color], color))
    output = [row[:] for row in grid]

    by_color = {
        color: _components(grid, color)
        for color in sorted(counts)
        if color != background
    }
    moving = {
        color: components
        for color, components in by_color.items()
        if len(components) >= 2
    }

    # Clear every moving color from its original corner position first.
    for color in moving:
        for row in range(height):
            for col in range(width):
                if grid[row][col] == color:
                    output[row][col] = background

    # Translate each disconnected object toward the center by its own box size.
    for color, components in moving.items():
        for component in components:
            rows = [row for row, _ in component]
            cols = [col for _, col in component]
            top, left = min(rows), min(cols)
            obj_height = max(rows) - top + 1
            obj_width = max(cols) - left + 1
            dr = obj_height if 2 * top < height else -obj_height
            dc = obj_width if 2 * left < width else -obj_width
            for row, col in component:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < height and 0 <= new_col < width:
                    output[new_row][new_col] = color

    return output
