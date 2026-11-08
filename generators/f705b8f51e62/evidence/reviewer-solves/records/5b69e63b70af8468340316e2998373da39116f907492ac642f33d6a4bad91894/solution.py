from collections import Counter, deque


def _components(grid):
    """Return 4-connected non-background components as normalized masks."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    components = []

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or seen[r][c]:
                continue

            q = deque([(r, c)])
            seen[r][c] = True
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))

            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            mask = tuple(
                tuple(1 if (rr, cc) in set(cells) else 0 for cc in range(c0, c1 + 1))
                for rr in range(r0, r1 + 1)
            )
            components.append((color, mask))

    return components


def solve(grid):
    components = _components(grid)
    counts = Counter(mask for _, mask in components)
    template = max(counts, key=lambda mask: (counts[mask], sum(map(sum, mask))))

    # The demonstrations contain one damaged/non-repeated copy.  Restore it to
    # the repeated template while preserving that copy's color.
    outliers = [(color, mask) for color, mask in components if mask != template]
    color = outliers[0][0] if outliers else components[0][0]
    return [[color if value else 0 for value in row] for row in template]
