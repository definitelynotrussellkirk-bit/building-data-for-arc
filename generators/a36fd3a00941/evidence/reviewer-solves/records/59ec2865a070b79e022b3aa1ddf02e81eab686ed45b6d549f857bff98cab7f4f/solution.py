from collections import deque


def solve(grid):
    """Pack non-background objects left-to-right in bottom-to-top reading order.

    Objects are the 4-connected nonzero components.  Each is cropped to its
    bounding box, components are ordered by decreasing bottom edge (then by
    their original left edge), and the crops are top-aligned with one blank
    column between adjacent objects.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            color = grid[row][col]
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
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [source_row[left : right + 1] for source_row in grid[top : bottom + 1]]
            objects.append((bottom, left, crop))

    if not objects:
        return []

    objects.sort(key=lambda item: (-item[0], item[1]))
    out_height = max(len(crop) for _, _, crop in objects)
    out_width = sum(len(crop[0]) for _, _, crop in objects) + len(objects) - 1
    output = [[0] * out_width for _ in range(out_height)]

    offset = 0
    for _, _, crop in objects:
        crop_width = len(crop[0])
        for r, crop_row in enumerate(crop):
            output[r][offset : offset + crop_width] = crop_row
        offset += crop_width + 1

    return output
