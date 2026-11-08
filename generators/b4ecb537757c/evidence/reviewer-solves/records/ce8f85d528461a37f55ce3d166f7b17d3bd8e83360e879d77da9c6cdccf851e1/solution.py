"""Move matching loose shapes into frames, using the interior rotation clue."""


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = {(row, col)}
            seen.add((row, col))
            pending = [(row, col)]
            while pending:
                rr, cc = pending.pop()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc),
                               (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        pending.append((nr, nc))
            components.append((color, cells))
    return components


def solve(grid):
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    frames = []
    for color, cells in _components(grid):
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        if bottom - top < 2 or right - left < 2:
            continue
        boundary = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
            if row in (top, bottom) or col in (left, right)
        }
        if cells != boundary:
            continue
        clues = [
            (row, col, grid[row][col])
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
            if grid[row][col] != 0
        ]
        if len(clues) == 1 and 1 <= clues[0][2] <= 4:
            frames.append((color, top, bottom, left, right, clues[0]))

    enclosed = {
        (row, col)
        for _, top, bottom, left, right, _ in frames
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }
    output = [row[:] for row in grid]

    for color, top, bottom, left, right, clue in frames:
        loose = {
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color and (row, col) not in enclosed
        }
        if not loose:
            raise ValueError("A frame has no matching loose shape")
        source_top = min(row for row, _ in loose)
        source_left = min(col for _, col in loose)
        shape = {(row - source_top, col - source_left)
                 for row, col in loose}
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(col for _, col in shape) + 1
        for _ in range(clue[2] - 1):
            shape = {(col, shape_height - 1 - row) for row, col in shape}
            shape_height, shape_width = shape_width, shape_height
        if shape_height > bottom - top - 1 or shape_width > right - left - 1:
            raise ValueError("The rotated shape does not fit its frame")

        for row, col in loose:
            output[row][col] = 0
        output[clue[0]][clue[1]] = 0
        for row, col in shape:
            output[top + 1 + row][left + 1 + col] = color

    return output
