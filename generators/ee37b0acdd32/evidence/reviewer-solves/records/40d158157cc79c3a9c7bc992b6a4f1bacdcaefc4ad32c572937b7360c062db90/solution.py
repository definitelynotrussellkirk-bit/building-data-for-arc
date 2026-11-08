from collections import deque


def solve(grid):
    """Keep the component-chain joining colors 1 and 2, recolored gray (8)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    component_at = [[-1] * width for _ in range(height)]
    components = []
    component_colors = []
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    # Maximal 4-connected, same-color non-background regions are graph nodes.
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or component_at[row][col] != -1:
                continue
            component_id = len(components)
            cells = []
            queue = deque([(row, col)])
            component_at[row][col] = component_id
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for dr, dc in directions:
                    nr, nc = current_row + dr, current_col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and component_at[nr][nc] == -1
                        and grid[nr][nc] == color
                    ):
                        component_at[nr][nc] = component_id
                        queue.append((nr, nc))
            components.append(cells)
            component_colors.append(color)

    starts = [i for i, color in enumerate(component_colors) if color == 1]
    goals = {i for i, color in enumerate(component_colors) if color == 2}
    if len(starts) != 1 or len(goals) != 1:
        raise ValueError("expected one color-1 component and one color-2 component")

    adjacency = [set() for _ in components]
    for row in range(height):
        for col in range(width):
            first = component_at[row][col]
            if first == -1:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    second = component_at[nr][nc]
                    if second != -1 and second != first:
                        adjacency[first].add(second)
                        adjacency[second].add(first)

    start = starts[0]
    goal = next(iter(goals))
    previous = {start: None}
    queue = deque([start])
    while queue and goal not in previous:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in previous:
                previous[neighbor] = current
                queue.append(neighbor)
    if goal not in previous:
        raise ValueError("color-1 and color-2 components are disconnected")

    path_components = set()
    current = goal
    while current is not None:
        path_components.add(current)
        current = previous[current]

    output = [[0] * width for _ in range(height)]
    for component_id in path_components:
        for row, col in components[component_id]:
            output[row][col] = 8
    return output
