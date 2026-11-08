"""Visible-example solution for the assigned ARC task.

The input contains two colored rectangular frames.  A unique marker inside each
frame points to the payload color (1 or 2); the marker also selects a geometric
transform.  The transformed payloads are recolored with their frame colors and
placed side by side in frame reading order.
"""

from collections import deque


def _rectangular_frames(grid):
    """Return hollow monochrome frames as (top, left, bottom, right, color)."""
    height = len(grid)
    width = len(grid[0])
    colors = {cell for row in grid for cell in row} - {0, 1, 2}
    frames = []

    for color in colors:
        cells = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if grid[r][c] == color
        ]
        if len(cells) < 8:
            continue

        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        if top == bottom or left == right:
            continue

        perimeter = []
        perimeter.extend((top, c) for c in range(left, right + 1))
        perimeter.extend((bottom, c) for c in range(left, right + 1))
        perimeter.extend((r, left) for r in range(top + 1, bottom))
        perimeter.extend((r, right) for r in range(top + 1, bottom))

        if all(grid[r][c] == color for r, c in perimeter):
            frames.append((top, left, bottom, right, color))

    return sorted(frames, key=lambda frame: (frame[0], frame[1]))


def _component(grid, start, color):
    """Four-connected component of *color* containing *start*."""
    height = len(grid)
    width = len(grid[0])
    seen = {start}
    queue = deque([start])

    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and (nr, nc) not in seen
                and grid[nr][nc] == color
            ):
                seen.add((nr, nc))
                queue.append((nr, nc))
    return seen


def _crop_mask(cells):
    """Crop a set of coordinates to a 0/1 mask."""
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    mask = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for r, c in cells:
        mask[r - top][c - left] = 1
    return mask


def _rotate_clockwise(mask):
    return [list(row) for row in zip(*mask[::-1])]


def _transform(mask, marker):
    if marker == 3:
        return mask
    if marker == 4:
        return _rotate_clockwise(mask)
    if marker == 5:
        return _rotate_clockwise(_rotate_clockwise(mask))
    if marker == 6:
        return [row[::-1] for row in mask]
    raise ValueError(f"unknown transform marker: {marker}")


def _payload_for_frame(grid, frame):
    top, left, bottom, right, frame_color = frame
    interior_cells = [
        (r, c)
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
    ]

    marker_cells = [
        (r, c)
        for r, c in interior_cells
        if grid[r][c] not in (0, 1, 2, frame_color)
    ]
    if len(marker_cells) != 1:
        raise ValueError("expected exactly one transform marker per frame")
    marker_pos = marker_cells[0]
    marker = grid[marker_pos[0]][marker_pos[1]]

    selector_neighbors = []
    mr, mc = marker_pos
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = mr + dr, mc + dc
        if top < nr < bottom and left < nc < right and grid[nr][nc] in (1, 2):
            selector_neighbors.append((nr, nc))
    if len(selector_neighbors) != 1:
        raise ValueError("expected marker to touch exactly one selector cell")

    selector_pos = selector_neighbors[0]
    selected_color = grid[selector_pos[0]][selector_pos[1]]
    selector_component = _component(grid, selector_pos, selected_color)
    payload_cells = {
        (r, c)
        for r, c in interior_cells
        if grid[r][c] == selected_color and (r, c) not in selector_component
    }
    if not payload_cells:
        raise ValueError("selected payload is empty")

    return frame_color, _transform(_crop_mask(payload_cells), marker)


def solve(grid):
    frames = _rectangular_frames(grid)
    if not frames:
        return []

    pieces = [_payload_for_frame(grid, frame) for frame in frames]
    output_height = max(len(mask) for _, mask in pieces)
    output_width = sum(len(mask[0]) for _, mask in pieces) + len(pieces) - 1
    output = [[0] * output_width for _ in range(output_height)]

    column = 0
    for frame_color, mask in pieces:
        row_offset = (output_height - len(mask)) // 2
        for r, row in enumerate(mask):
            for c, occupied in enumerate(row):
                if occupied:
                    output[row_offset + r][column + c] = frame_color
        column += len(mask[0]) + 1

    return output
