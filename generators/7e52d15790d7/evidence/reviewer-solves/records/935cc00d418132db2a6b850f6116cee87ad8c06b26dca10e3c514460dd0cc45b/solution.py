"""Visible-example-only solution for blind task 7e52d15790d7."""

from collections import deque


def solve(grid):
    """Crop nonzero objects and pack them by decreasing bounding-box area."""
    if not grid or not grid[0]:
        return []

    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    objects = []

    for r0 in range(h):
        for c0 in range(w):
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
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and not seen[rr][cc]
                        and grid[rr][cc] == color
                    ):
                        seen[rr][cc] = True
                        queue.append((rr, cc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [row[left : right + 1] for row in grid[top : bottom + 1]]
            box_height = bottom - top + 1
            box_width = right - left + 1
            objects.append(
                {
                    "area": box_height * box_width,
                    "color": color,
                    "top": top,
                    "left": left,
                    "crop": crop,
                    "height": box_height,
                    "width": box_width,
                }
            )

    if not objects:
        return []

    objects.sort(key=lambda obj: (-obj["area"], obj["color"], obj["top"], obj["left"]))
    out_height = max(obj["height"] for obj in objects)
    out_width = sum(obj["width"] for obj in objects) + len(objects) - 1
    output = [[0] * out_width for _ in range(out_height)]

    offset = 0
    for obj in objects:
        for r, row in enumerate(obj["crop"]):
            output[r][offset : offset + obj["width"]] = row
        offset += obj["width"] + 1

    return output
