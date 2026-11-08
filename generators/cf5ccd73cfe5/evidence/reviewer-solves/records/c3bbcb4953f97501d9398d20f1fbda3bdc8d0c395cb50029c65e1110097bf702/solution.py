"""Visible-only solution for the assigned ARC puzzle."""

from collections import Counter, deque


def _components_by_color(grid, background):
    height = len(grid)
    width = len(grid[0])
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            component = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.add((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            yield color, component


def _rectangle_perimeter(top, left, bottom, right):
    cells = set()
    for col in range(left, right + 1):
        cells.add((top, col))
        cells.add((bottom, col))
    for row in range(top + 1, bottom):
        cells.add((row, left))
        cells.add((row, right))
    return cells


def solve(grid):
    """Scale the separate motif into the interior of the rectangular frame."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    frame_candidates = []
    for color, component in _components_by_color(grid, background):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if bottom - top < 2 or right - left < 2:
            continue
        if component == _rectangle_perimeter(top, left, bottom, right):
            area = (bottom - top + 1) * (right - left + 1)
            frame_candidates.append((area, color, top, left, bottom, right))

    if not frame_candidates:
        raise ValueError("no rectangular frame found")

    _, frame_color, top, left, bottom, right = max(frame_candidates)
    frame_height = bottom - top + 1
    frame_width = right - left + 1
    inner_height = frame_height - 2
    inner_width = frame_width - 2

    motif_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
        and not (top <= row <= bottom and left <= col <= right)
    ]
    if not motif_cells:
        raise ValueError("no motif found outside the frame")

    motif_top = min(row for row, _ in motif_cells)
    motif_bottom = max(row for row, _ in motif_cells)
    motif_left = min(col for _, col in motif_cells)
    motif_right = max(col for _, col in motif_cells)
    motif = [
        grid[row][motif_left : motif_right + 1]
        for row in range(motif_top, motif_bottom + 1)
    ]
    motif_height = len(motif)
    motif_width = len(motif[0])

    if inner_height % motif_height or inner_width % motif_width:
        raise ValueError("motif does not scale evenly into the frame interior")

    row_scale = inner_height // motif_height
    col_scale = inner_width // motif_width
    output = [[background for _ in range(frame_width)] for _ in range(frame_height)]

    for col in range(frame_width):
        output[0][col] = frame_color
        output[-1][col] = frame_color
    for row in range(1, frame_height - 1):
        output[row][0] = frame_color
        output[row][-1] = frame_color

    for motif_row in range(motif_height):
        for motif_col in range(motif_width):
            value = motif[motif_row][motif_col]
            start_row = 1 + motif_row * row_scale
            start_col = 1 + motif_col * col_scale
            for row in range(start_row, start_row + row_scale):
                for col in range(start_col, start_col + col_scale):
                    output[row][col] = value

    return output
