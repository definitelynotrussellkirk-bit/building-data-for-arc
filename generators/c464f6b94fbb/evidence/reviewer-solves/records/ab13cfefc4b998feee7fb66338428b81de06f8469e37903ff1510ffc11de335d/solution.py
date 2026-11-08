from collections import deque


def solve(grid):
    """Pack nonzero objects left-to-right by decreasing pixel count.

    Objects are 4-connected components of a single nonzero color.  Each object is
    cropped to its bounding box, components of equal size retain reading order,
    and one background column separates neighboring crops.  Crops are top-aligned.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    objects = []

    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or seen[r0][c0]:
                continue

            queue = deque([(r0, c0)])
            seen[r0][c0] = True
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
            for r, c in cells:
                crop[r - top][c - left] = color

            objects.append(
                {
                    "size": len(cells),
                    "top": top,
                    "left": left,
                    "crop": crop,
                }
            )

    if not objects:
        return []

    objects.sort(key=lambda obj: (-obj["size"], obj["top"], obj["left"]))
    out_height = max(len(obj["crop"]) for obj in objects)
    out_width = sum(len(obj["crop"][0]) for obj in objects) + len(objects) - 1
    output = [[0] * out_width for _ in range(out_height)]

    offset = 0
    for obj in objects:
        crop = obj["crop"]
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                output[r][offset + c] = value
        offset += len(crop[0]) + 1

    return output
