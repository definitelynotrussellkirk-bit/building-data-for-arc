from collections import Counter, deque


def solve(grid):
    """Restore marked rectangular frames while leaving unmarked objects alone."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    counts = Counter(value for row in grid for value in row if value != 0)
    if len(counts) < 2:
        return out

    # The damage/annotation color is the rare non-background color.  It appears
    # inside one or more otherwise single-colored rectangular objects.
    marker = min(counts, key=lambda value: (counts[value], value))

    def components(color):
        seen = set()
        for r in range(height):
            for c in range(width):
                if grid[r][c] != color or (r, c) in seen:
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
                            and grid[nr][nc] == color
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            queue.append((nr, nc))
                yield cells

    repaired = set()
    for color in counts:
        if color == marker:
            continue
        for cells in components(color):
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            if r1 - r0 < 2 or c1 - c0 < 2:
                continue

            perimeter = (
                [(r0, c) for c in range(c0, c1 + 1)]
                + [(r1, c) for c in range(c0, c1 + 1)]
                + [(r, c0) for r in range(r0 + 1, r1)]
                + [(r, c1) for r in range(r0 + 1, r1)]
            )
            if any(grid[r][c] != color for r, c in perimeter):
                continue
            if not any(
                grid[r][c] == marker
                for r in range(r0 + 1, r1)
                for c in range(c0 + 1, c1)
            ):
                continue

            box = (r0, r1, c0, c1, color)
            if box in repaired:
                continue
            repaired.add(box)
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if r in (r0, r1) or c in (c0, c1):
                        out[r][c] = color
                    else:
                        out[r][c] = 0

    return out
