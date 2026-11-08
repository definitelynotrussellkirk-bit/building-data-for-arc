from __future__ import annotations


def _run_length(grid, color, row, col, dr, dc):
    height = len(grid)
    width = len(grid[0])
    length = 0
    while 0 <= row < height and 0 <= col < width and grid[row][col] == color:
        length += 1
        row += dr
        col += dc
    return length


def _color_info(grid, color):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    max_dim = max(max(rows) - min(rows) + 1, max(cols) - min(cols) + 1)

    arm = 0
    for row, col in cells:
        for dr in (-1, 1):
            for dc in (-1, 1):
                arm = max(
                    arm,
                    min(
                        _run_length(grid, color, row, col, 0, dc),
                        _run_length(grid, color, row, col, dr, 0),
                    ),
                )
    return {"color": color, "max_dim": max_dim, "arm": arm}


def _corner_l_cells(size, arm):
    cells = set()
    arm = min(size, arm)
    for step in range(arm):
        cells.update(
            {
                (0, step),
                (step, 0),
                (0, size - 1 - step),
                (step, size - 1),
                (size - 1, step),
                (size - 1 - step, 0),
                (size - 1, size - 1 - step),
                (size - 1 - step, size - 1),
            }
        )
    return cells


def solve(grid):
    background = grid[0][0]
    colors = sorted({value for row in grid for value in row if value != background})
    infos = [_color_info(grid, color) for color in colors]

    has_center = any(info["max_dim"] == 1 for info in infos)
    first_size = 1 if has_center else 3
    ring_sizes = [first_size + 2 * index for index in range(len(infos))]
    available = list(ring_sizes)

    exact = [info for info in infos if info["max_dim"] in ring_sizes]
    loose = [info for info in infos if info["max_dim"] not in ring_sizes]
    assignments = []
    for info in loose + sorted(exact, key=lambda item: -item["max_dim"]):
        ring = next(size for size in available if size >= info["max_dim"])
        available.remove(ring)
        assignments.append((info, ring))

    output_size = max(ring_sizes)
    middle = output_size // 2
    output = [[background for _ in range(output_size)] for _ in range(output_size)]
    for info, ring in assignments:
        offset = middle - ring // 2
        for row, col in _corner_l_cells(ring, info["arm"]):
            output[offset + row][offset + col] = info["color"]
    return output
