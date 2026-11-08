def solve(grid):
    """Join the longest simple route from the red square with orange corridors."""
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")

    nodes = []
    start = None
    covered = set()
    for row in range(height - 1):
        for col in range(width - 1):
            color = grid[row][col]
            cells = [(row + dr, col + dc) for dr in (0, 1) for dc in (0, 1)]
            if color in (2, 8) and not any(cell in covered for cell in cells):
                if all(grid[r][c] == color for r, c in cells):
                    if color == 2:
                        if start is not None:
                            raise ValueError("Expected one red starting square")
                        start = len(nodes)
                    nodes.append((row, col))
                    covered.update(cells)
    if start is None:
        raise ValueError("Missing red starting square")

    # The visible routes connect adjacent aligned squares, never jumping over one.
    neighbors = [[] for _ in nodes]
    for index, (row, col) in enumerate(nodes):
        nearest = {}
        for other, (r, c) in enumerate(nodes):
            if index == other:
                continue
            if r == row:
                direction = 0 if c > col else 2  # right, then left
            elif c == col:
                direction = 1 if r > row else 3  # down, then up
            else:
                continue
            distance = abs(r - row) + abs(c - col)
            if direction not in nearest or distance < nearest[direction][0]:
                nearest[direction] = (distance, other)
        neighbors[index] = [(direction, nearest[direction][1]) for direction in sorted(nearest)]

    best_path = [start]
    best_directions = ()

    def visit(path, directions, used):
        nonlocal best_path, best_directions
        if len(path) > len(best_path) or (
            len(path) == len(best_path) and directions < best_directions
        ):
            best_path = path[:]
            best_directions = directions
        for direction, other in neighbors[path[-1]]:
            if other not in used:
                visit(path + [other], directions + (direction,), used | {other})

    visit([start], (), {start})
    output = [row[:] for row in grid]
    for first, second in zip(best_path, best_path[1:]):
        row, col = nodes[first]
        r, c = nodes[second]
        if row == r:
            for x in range(min(col, c) + 2, max(col, c)):
                output[row][x] = output[row + 1][x] = 7
        else:
            for y in range(min(row, r) + 2, max(row, r)):
                output[y][col] = output[y][col + 1] = 7
    return output
