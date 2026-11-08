"""Visible-example solution for blind task 7e52d15790d7."""

from collections import deque


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    result = []

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue

            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
            result.append(
                {
                    "crop": crop,
                    "area": (r1 - r0 + 1) * (c1 - c0 + 1),
                    "right": c1,
                    "bottom": r1,
                }
            )
    return result


def solve(grid):
    """Crop, rank, and horizontally concatenate all non-background objects."""
    objects = _components(grid)
    if not objects:
        return []

    # The visible examples rank by bounding-box area.  Their only tied pair is
    # resolved by the object farther to the right in the source grid.
    objects.sort(key=lambda obj: (-obj["area"], -obj["right"], -obj["bottom"]))

    out_h = max(len(obj["crop"]) for obj in objects)
    out_w = sum(len(obj["crop"][0]) for obj in objects) + len(objects) - 1
    out = [[0] * out_w for _ in range(out_h)]

    x = 0
    for index, obj in enumerate(objects):
        crop = obj["crop"]
        for r, row in enumerate(crop):
            out[r][x : x + len(row)] = row
        x += len(crop[0])
        if index + 1 < len(objects):
            x += 1
    return out
