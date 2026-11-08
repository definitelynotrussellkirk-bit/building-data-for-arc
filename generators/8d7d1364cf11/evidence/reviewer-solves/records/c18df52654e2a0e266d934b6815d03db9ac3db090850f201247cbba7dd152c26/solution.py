"""Visible-example solution for the generated stamping puzzle."""


def _components(grid, background=4):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == background or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col, grid[row][col]))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and grid[nr][nc] != background
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def solve(grid):
    height, width = len(grid), len(grid[0])
    components = _components(grid)
    shapes = [component for component in components if len(component) > 1]
    dots = [component[0] for component in components if len(component) == 1]

    # The output clears the original scene.  A singleton whose color occurs in
    # a source shape becomes the alignment point for a translated copy of that
    # complete shape.  Singleton colors absent from every source are decoys.
    output = [[4 for _ in range(width)] for _ in range(height)]
    indexed_cells = [
        (shape, row, col, color)
        for shape in shapes
        for row, col, color in shape
    ]
    for dot_r, dot_c, dot_color in dots:
        match = next(
            (
                (shape, anchor_r, anchor_c)
                for shape, anchor_r, anchor_c, color in indexed_cells
                if color == dot_color
            ),
            None,
        )
        if match is None:
            continue
        shape, anchor_r, anchor_c = match
        for row, col, color in shape:
            nr = dot_r + row - anchor_r
            nc = dot_c + col - anchor_c
            if 0 <= nr < height and 0 <= nc < width:
                output[nr][nc] = color
    return output
