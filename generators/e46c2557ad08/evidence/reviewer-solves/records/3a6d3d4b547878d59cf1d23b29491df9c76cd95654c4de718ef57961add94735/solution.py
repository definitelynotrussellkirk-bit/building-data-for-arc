def solve(grid):
    """Recolor each isolated horizontal gray domino (5,5) cyan (8)."""
    output = [list(row) for row in grid]
    remaining = {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 5
    }

    while remaining:
        start = remaining.pop()
        component = {start}
        frontier = [start]
        while frontier:
            row, column = frontier.pop()
            for point in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    frontier.append(point)

        if len(component) == 2 and len({row for row, _ in component}) == 1:
            for row, column in component:
                output[row][column] = 8

    return output
