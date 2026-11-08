from collections import deque


def _components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            todo = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while todo:
                r, c = todo.popleft()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append(cells)
    return components


def _is_filled_rectangle(cells, box_height, box_width):
    return len(cells) == box_height * box_width


def _is_square_frame(cells, min_row, max_row, min_col, max_col):
    side = max_row - min_row + 1
    if side != max_col - min_col + 1 or side < 2:
        return False
    expected = {
        (r, c)
        for r in range(min_row, max_row + 1)
        for c in range(min_col, max_col + 1)
        if r in (min_row, max_row) or c in (min_col, max_col)
    }
    return set(cells) == expected


def _replacement_color(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    min_row, max_row = min(rows), max(rows)
    min_col, max_col = min(cols), max(cols)
    box_height = max_row - min_row + 1
    box_width = max_col - min_col + 1
    size = len(cells)

    # The examples use four geometric glyphs for colors 2, 3, 4, and 5.
    if size == 1:
        return 5
    if size == 5 and {box_height, box_width} == {3}:
        return 2  # equal-armed L pentomino
    if size == 6 and {box_height, box_width} == {2, 3} and _is_filled_rectangle(
        cells, box_height, box_width
    ):
        return 3
    if size == 4 and (
        (box_height == 1 and box_width == 4)
        or (box_height == 4 and box_width == 1)
    ):
        return 4

    # The same four labels can be encoded as concentric square frames.  Their
    # side lengths in the demonstrations are 13, 9, 5, and 1 respectively.
    if _is_square_frame(cells, min_row, max_row, min_col, max_col):
        side = box_height
        if side >= 5 and (side - 1) % 4 == 0:
            return 5 - (side - 1) // 4

    return None


def solve(grid):
    output = [row[:] for row in grid]
    for cells in _components(grid):
        replacement = _replacement_color(cells)
        if replacement is None:
            continue
        for row, col in cells:
            output[row][col] = replacement
    return output
