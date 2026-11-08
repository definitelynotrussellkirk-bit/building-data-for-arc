"""Infer a recoloring from monochromatic connected-component sizes."""


def solve(grid):
    """Keep one largest component per input color, breaking ties in scan order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()
    components_by_color = {}

    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            pending = [(row, column)]
            seen.add((row, column))
            component = []
            while pending:
                current_row, current_column = pending.pop()
                component.append((current_row, current_column))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    neighbor_row = current_row + dr
                    neighbor_column = current_column + dc
                    neighbor = (neighbor_row, neighbor_column)
                    if (
                        0 <= neighbor_row < height
                        and 0 <= neighbor_column < width
                        and neighbor not in seen
                        and grid[neighbor_row][neighbor_column] == color
                    ):
                        seen.add(neighbor)
                        pending.append(neighbor)
            components_by_color.setdefault(color, []).append(component)

    for components in components_by_color.values():
        selected = max(range(len(components)), key=lambda index: len(components[index]))
        for index, component in enumerate(components):
            replacement = 8 if index == selected else 2
            for row, column in component:
                output[row][column] = replacement

    return output
