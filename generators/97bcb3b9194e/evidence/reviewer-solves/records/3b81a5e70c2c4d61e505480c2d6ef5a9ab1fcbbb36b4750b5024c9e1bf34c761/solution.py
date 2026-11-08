from collections import Counter, deque


def solve(grid):
    """Extract the non-background object with the fewest off-base pixels."""
    if not grid or not grid[0]:
        return []

    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    non_background_counts = Counter(
        value for row in grid for value in row if value != background
    )
    if not non_background_counts:
        return [row[:] for row in grid]
    base = non_background_counts.most_common(1)[0][0]

    seen = set()
    candidates = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == background or (r, c) in seen:
                continue

            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != background
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            r0 = min(cr for cr, _ in cells)
            r1 = max(cr for cr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
            off_base = sum(value != base for row in crop for value in row)
            area = (r1 - r0 + 1) * (c1 - c0 + 1)
            candidates.append((off_base, -area, r0, c0, crop))

    return min(candidates, key=lambda item: item[:4])[4]
