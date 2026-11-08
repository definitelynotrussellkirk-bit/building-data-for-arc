"""A rule inferred from the three visible training pairs only."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    remaining = {
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value != 0
    }

    objects = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        component = {first}
        frontier = [first]
        while frontier:
            row, col = frontier.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    frontier.append(neighbor)
        objects.append(component)

    if len(objects) < 2:
        raise ValueError("The inferred rule requires at least two objects.")
    objects.sort(key=lambda component: (len(component), min(component)))
    selected = objects[1]
    top = min(row for row, _ in selected)
    left = min(col for _, col in selected)

    output = [[0] * width for _ in range(height)]
    for row, col in selected:
        target_row = top + 2 * (row - top)
        target_col = left + 2 * (col - left)
        for dr in range(2):
            for dc in range(2):
                out_row = target_row + dr
                out_col = target_col + dc
                if out_row < height and out_col < width:
                    output[out_row][out_col] = 8
    return output
