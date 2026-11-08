from collections import deque


def solve(grid):
    """Recolor a tree-shaped track around the two marked positions."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }

    def neighbors(cell):
        row, col = cell
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            other = (row + drow, col + dcol)
            if other in cells:
                yield other

    markers = {
        value: (row, col)
        for row in range(height)
        for col in range(width)
        if (value := grid[row][col]) in (1, 2)
    }
    if set(markers) != {1, 2}:
        return [list(row) for row in grid]

    start, goal = markers[2], markers[1]
    parent = {start: None}
    queue = deque([start])
    while queue and goal not in parent:
        cell = queue.popleft()
        for other in neighbors(cell):
            if other not in parent:
                parent[other] = cell
                queue.append(other)
    if goal not in parent:
        return [list(row) for row in grid]

    path = []
    cell = goal
    while cell is not None:
        path.append(cell)
        cell = parent[cell]
    path.reverse()
    path_set = set(path)

    output = [
        [4 if value == 5 else value for value in row]
        for row in grid
    ]

    def color_terminal_branch(oriented_path, color):
        # Walk from the marker toward the other marker.  The first path cell
        # with a side branch is the marker's junction; its off-path subtree is
        # the terminal arm belonging to that marker.
        for anchor in oriented_path:
            side_roots = [other for other in neighbors(anchor) if other not in path_set]
            if not side_roots:
                continue
            seen = set(path_set)
            stack = side_roots[:]
            while stack:
                branch_cell = stack.pop()
                if branch_cell in seen:
                    continue
                seen.add(branch_cell)
                row, col = branch_cell
                if grid[row][col] == 5:
                    output[row][col] = color
                stack.extend(neighbors(branch_cell))
            return

    color_terminal_branch(path, 2)
    color_terminal_branch(list(reversed(path)), 1)
    return output
