"""Visible-example solution for the generated ARC task.

The input contains separated monochromatic objects.  The output crops each
object, orders objects by enclosed-hole count and then by color, and packs the
crops left-to-right with a one-column background separator.
"""

from collections import deque


def _components(grid):
    """Return non-background 4-connected monochromatic components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    found = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append((color, cells))

    return found


def _crop_component(color, cells):
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)

    crop = [
        [0 for _ in range(max_col - min_col + 1)]
        for _ in range(max_row - min_row + 1)
    ]
    for row, col in cells:
        crop[row - min_row][col - min_col] = color
    return crop


def _enclosed_zero_regions(crop):
    """Count 4-connected zero regions that do not touch the crop boundary."""
    height = len(crop)
    width = len(crop[0]) if height else 0
    seen = set()
    enclosed = 0

    for row in range(height):
        for col in range(width):
            if crop[row][col] != 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            touches_edge = False
            while queue:
                r, c = queue.popleft()
                if r in (0, height - 1) or c in (0, width - 1):
                    touches_edge = True
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and crop[nr][nc] == 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            if not touches_edge:
                enclosed += 1

    return enclosed


def solve(grid):
    """Crop, rank, and horizontally pack the input's colored objects."""
    if not grid or not grid[0]:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    objects = []
    for color, cells in _components(grid):
        crop = _crop_component(color, cells)
        objects.append((_enclosed_zero_regions(crop), color, crop))

    if not objects:
        return []

    objects.sort(key=lambda item: (item[0], item[1]))
    crops = [crop for _, _, crop in objects]
    output_height = max(len(crop) for crop in crops)
    output_width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0 for _ in range(output_width)] for _ in range(output_height)]

    offset = 0
    for crop in crops:
        for row, values in enumerate(crop):
            output[row][offset : offset + len(values)] = values
        offset += len(crop[0]) + 1

    return output
