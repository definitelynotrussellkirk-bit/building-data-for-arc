from collections import deque


def solve(grid):
    """Fill the largest non-solid monochrome rectangle by painted-cell count."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    candidates = []

    for r in range(height):
        for c in range(width):
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
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            bbox_area = (r1 - r0 + 1) * (c1 - c0 + 1)

            # Fully filled rectangles are distractors; incomplete rectangles compete
            # by their actual number of colored cells, not by bounding-box area.
            if len(cells) < bbox_area:
                candidates.append((len(cells), r0, c0, r1, c1, color))

    if not candidates:
        return out

    _, r0, c0, r1, c1, color = max(candidates)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = color
    return out
