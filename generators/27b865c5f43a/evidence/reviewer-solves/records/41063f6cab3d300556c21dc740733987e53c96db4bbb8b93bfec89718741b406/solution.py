from collections import deque


def _objects(grid):
    """Return non-background monochrome components ordered left-to-right."""
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

            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            mask = [[False] * 3 for _ in range(3)]
            for r, c in cells:
                rr, cc = r - top, c - left
                if rr >= 3 or cc >= 3:
                    raise ValueError("object does not fit the inferred 3x3 tile")
                mask[rr][cc] = True
            found.append((left, top, bottom, right, mask))

    found.sort(key=lambda item: (item[0], item[1]))
    return [item[-1] for item in found]


def solve(grid):
    """Build the pairwise-union table of the three cropped input shapes."""
    shapes = _objects(grid)
    if len(shapes) != 3:
        raise ValueError(f"expected three objects, found {len(shapes)}")

    tile = 3
    gap = 1
    size = len(shapes) * tile + (len(shapes) - 1) * gap
    output = [[0] * size for _ in range(size)]

    for object_row, first in enumerate(shapes):
        for object_col, second in enumerate(shapes):
            row0 = object_row * (tile + gap)
            col0 = object_col * (tile + gap)
            for row in range(tile):
                for col in range(tile):
                    if first[row][col] or second[row][col]:
                        output[row0 + row][col0 + col] = 8

    return output
