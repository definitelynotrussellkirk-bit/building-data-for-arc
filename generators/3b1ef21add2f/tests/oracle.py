"""Independent grid-loop oracle and observations for the red-window task.

This file deliberately imports no generator or shared drawing helpers.
All window membership is computed from the original input.
"""


def red_windows(grid):
    """Return all top-left coordinates of complete red 2x2 neighborhoods."""
    found = []
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            if (grid[row][col] == 2 and grid[row + 1][col] == 2
                    and grid[row][col + 1] == 2 and grid[row + 1][col + 1] == 2):
                found.append((row, col))
    return found


def window_cells(grid):
    cells = set()
    for row, col in red_windows(grid):
        cells.update(((row, col), (row + 1, col),
                      (row, col + 1), (row + 1, col + 1)))
    return cells


def solve(grid):
    """Recolor the union of windows found in input, preserving every other cell."""
    cells = window_cells(grid)
    return [[3 if (row, col) in cells else value
             for col, value in enumerate(values)]
            for row, values in enumerate(grid)]


def red_components(grid):
    """Orthogonally connected red cells, used only to observe generated lessons."""
    unseen = {(row, col) for row, values in enumerate(grid)
              for col, value in enumerate(values) if value == 2}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component, pending = {start}, [start]
        while pending:
            row, col = pending.pop()
            for neighbor in ((row - 1, col), (row + 1, col),
                             (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        components.append(component)
    return components


def diagnostic_features(grid):
    """Observe the five promised rich-scene features without generator metadata."""
    windows = red_windows(grid)
    sets = [{(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}
            for row, col in windows]
    changed = window_cells(grid)
    components = red_components(grid)
    return {
        "overlap": any(left & right for index, left in enumerate(sets)
                       for right in sets[index + 1:]),
        "attached_red_survives": any(part & changed and part - changed
                                      for part in components),
        "separate_square": any(len(part) == 4 and part <= changed
                               for part in components),
        "red_tetromino_without_square": any(len(part) == 4 and not part & changed
                                            for part in components),
        "nonred_square": any(
            grid[row][col] not in (0, 2)
            and grid[row][col] == grid[row + 1][col]
            == grid[row][col + 1] == grid[row + 1][col + 1]
            for row in range(len(grid) - 1) for col in range(len(grid[0]) - 1)),
    }
