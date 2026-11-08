from collections import deque


_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _same_color_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells = set()
            while queue:
                row, col = queue.popleft()
                cells.add((row, col))
                for drow, dcol in _DIR4:
                    nr, nc = row + drow, col + dcol
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield color, cells


def _encloses_hole(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)

    nonshape = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if (row, col) not in cells
    }
    if not nonshape:
        return False

    reachable = set()
    queue = deque()
    for cell in nonshape:
        row, col = cell
        if row in (r0, r1) or col in (c0, c1):
            reachable.add(cell)
            queue.append(cell)

    while queue:
        row, col = queue.popleft()
        for drow, dcol in _DIR4:
            nxt = (row + drow, col + dcol)
            if nxt in nonshape and nxt not in reachable:
                reachable.add(nxt)
                queue.append(nxt)

    return bool(nonshape - reachable)


def solve(grid):
    """Erase each colored component unless its outline encloses a hole."""
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in _same_color_components(grid):
        if _encloses_hole(cells):
            for row, col in cells:
                output[row][col] = color
    return output
