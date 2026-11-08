"""Visible-only ARC solver for the prepared blind challenge."""


def _blocks(grid):
    """Return (color, top_row, left_col) for each isolated 2x2 marker."""
    height = len(grid)
    width = len(grid[0])
    found = []
    for row in range(height - 1):
        for col in range(width - 1):
            color = grid[row][col]
            if color not in (2, 8):
                continue
            if not all(
                grid[r][c] == color
                for r in (row, row + 1)
                for c in (col, col + 1)
            ):
                continue
            # Keep only the top-left cell of the 2x2 object.
            if row > 0 and grid[row - 1][col] == color:
                continue
            if col > 0 and grid[row][col - 1] == color:
                continue
            found.append((color, row, col))
    return found


def _visibility_graph(blocks):
    """Nearest visible block in each cardinal direction, in tie-break order."""
    directions = (
        ("right", 0, 1),
        ("down", 1, 0),
        ("left", 0, -1),
        ("up", -1, 0),
    )
    graph = [{} for _ in blocks]

    for index, (_, row, col) in enumerate(blocks):
        for name, drow, dcol in directions:
            candidates = []
            for other, (_, other_row, other_col) in enumerate(blocks):
                if other == index:
                    continue
                if drow == 0:
                    if other_row != row or (other_col - col) * dcol <= 0:
                        continue
                    distance = abs(other_col - col)
                else:
                    if other_col != col or (other_row - row) * drow <= 0:
                        continue
                    distance = abs(other_row - row)
                candidates.append((distance, other))
            if candidates:
                graph[index][name] = min(candidates)[1]
    return graph


def _longest_path(blocks, graph):
    """Longest simple visibility path from the red block; first tie wins."""
    start = next(i for i, (color, _, _) in enumerate(blocks) if color == 2)
    direction_order = ("right", "down", "left", "up")
    best = []

    def visit(path):
        nonlocal best
        current = path[-1]
        choices = []
        for direction in direction_order:
            neighbor = graph[current].get(direction)
            if neighbor is not None and neighbor not in path:
                choices.append(neighbor)

        if not choices:
            if len(path) > len(best):
                best = path.copy()
            return

        for neighbor in choices:
            visit(path + [neighbor])

    visit([start])
    return best


def _draw_connection(output, first, second):
    _, row_a, col_a = first
    _, row_b, col_b = second

    if row_a == row_b:
        left = min(col_a, col_b) + 2
        right = max(col_a, col_b)
        for row in (row_a, row_a + 1):
            for col in range(left, right):
                output[row][col] = 7
    else:
        top = min(row_a, row_b) + 2
        bottom = max(row_a, row_b)
        for row in range(top, bottom):
            for col in (col_a, col_a + 1):
                output[row][col] = 7


def solve(grid):
    blocks = _blocks(grid)
    graph = _visibility_graph(blocks)
    path = _longest_path(blocks, graph)

    output = [row[:] for row in grid]
    for first_index, second_index in zip(path, path[1:]):
        _draw_connection(output, blocks[first_index], blocks[second_index])
    return output
