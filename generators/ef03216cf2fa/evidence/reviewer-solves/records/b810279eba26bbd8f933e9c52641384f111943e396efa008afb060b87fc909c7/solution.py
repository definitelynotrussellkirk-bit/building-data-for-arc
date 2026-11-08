from collections import deque


def _components(grid):
    """Return same-colour 4-connected nonzero objects in row-major order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
            for r, c in cells:
                crop[r - top][c - left] = colour
            objects.append((len(cells), top, left, crop))

    return objects


def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def solve(grid):
    objects = _components(grid)
    if not objects:
        return []

    # Largest objects first; Python's stable ordering preserves row-major order
    # for equal cell counts via the explicit top/left keys.
    objects.sort(key=lambda item: (-item[0], item[1], item[2]))

    normalized = []
    canvas_width = 0
    for _, _, _, crop in objects:
        height = len(crop)
        width = len(crop[0])
        canvas_width = max(canvas_width, height, width)
        normalized.append(_rotate_clockwise(crop) if height > width else crop)

    output = []
    separator = [0] * canvas_width
    for index, crop in enumerate(normalized):
        output.extend(row + [0] * (canvas_width - len(row)) for row in crop)
        if index + 1 < len(normalized):
            output.append(separator.copy())
    return output
