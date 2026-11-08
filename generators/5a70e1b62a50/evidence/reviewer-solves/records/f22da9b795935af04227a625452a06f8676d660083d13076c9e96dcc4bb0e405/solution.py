from collections import Counter, deque


def solve(grid):
    """Fill 4-connected background holes with the color surrounding each hole."""
    out = [row[:] for row in grid]
    if not out or not out[0]:
        return out

    height, width = len(out), len(out[0])
    background = 0
    exterior = [[False] * width for _ in range(height)]
    queue = deque()

    def add_exterior(row, col):
        if out[row][col] == background and not exterior[row][col]:
            exterior[row][col] = True
            queue.append((row, col))

    for row in range(height):
        add_exterior(row, 0)
        if width > 1:
            add_exterior(row, width - 1)
    for col in range(width):
        add_exterior(0, col)
        if height > 1:
            add_exterior(height - 1, col)

    while queue:
        row, col = queue.popleft()
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + drow, col + dcol
            if 0 <= nr < height and 0 <= nc < width:
                add_exterior(nr, nc)

    visited_hole = [[False] * width for _ in range(height)]
    for start_row in range(height):
        for start_col in range(width):
            if (
                out[start_row][start_col] != background
                or exterior[start_row][start_col]
                or visited_hole[start_row][start_col]
            ):
                continue

            component = []
            boundary_colors = Counter()
            queue.append((start_row, start_col))
            visited_hole[start_row][start_col] = True

            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + drow, col + dcol
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    value = out[nr][nc]
                    if value == background:
                        if not exterior[nr][nc] and not visited_hole[nr][nc]:
                            visited_hole[nr][nc] = True
                            queue.append((nr, nc))
                    else:
                        boundary_colors[value] += 1

            if boundary_colors:
                fill_color = boundary_colors.most_common(1)[0][0]
                for row, col in component:
                    out[row][col] = fill_color

    return out
