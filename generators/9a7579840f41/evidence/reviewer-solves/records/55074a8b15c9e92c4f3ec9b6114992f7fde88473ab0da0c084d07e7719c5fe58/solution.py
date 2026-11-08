def solve(grid):
    height = len(grid)
    width = len(grid[0])
    cardinals = ((-1, 0), (1, 0), (0, -1), (0, 1))

    template = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 4
    ]
    top = min(row for row, _ in template)
    left = min(col for _, col in template)
    shape = [(row - top, col - left) for row, col in template]

    start = next(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7
    )
    wire = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }

    adjacent = [
        (start[0] + dr, start[1] + dc)
        for dr, dc in cardinals
        if (start[0] + dr, start[1] + dc) in wire
    ]
    previous = start
    current = adjacent[0]
    path = []
    seen = set()
    while True:
        path.append(current)
        seen.add(current)
        next_cells = [
            (current[0] + dr, current[1] + dc)
            for dr, dc in cardinals
            if (current[0] + dr, current[1] + dc) in wire
            and (current[0] + dr, current[1] + dc) != previous
            and (current[0] + dr, current[1] + dc) not in seen
        ]
        if not next_cells:
            break
        previous, current = current, next_cells[0]

    turns = []
    for before, cell, after in zip(path, path[1:], path[2:]):
        incoming = (cell[0] - before[0], cell[1] - before[1])
        outgoing = (after[0] - cell[0], after[1] - cell[1])
        if incoming != outgoing:
            turns.append(cell)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for turn_row, turn_col in turns:
        for shape_row, shape_col in shape:
            output[turn_row + shape_row][turn_col + shape_col] = 4
    return output
