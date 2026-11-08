from collections import Counter, deque


def _largest_nonbackground_component(grid, background):
    rows, cols = len(grid), len(grid[0])
    seen = set()
    best = None

    for r in range(rows):
        for c in range(cols):
            color = grid[r][c]
            if color == background or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            candidate = (len(cells), color, cells)
            if best is None or candidate[0] > best[0]:
                best = candidate

    if best is None:
        raise ValueError("grid contains no foreground object")
    return best[1], best[2]


def solve(grid):
    """Extend the main rectangle into a cross, with markers cutting arm lanes."""
    rows, cols = len(grid), len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    block_color, block_cells = _largest_nonbackground_component(grid, background)

    r0 = min(r for r, _ in block_cells)
    r1 = max(r for r, _ in block_cells)
    c0 = min(c for _, c in block_cells)
    c1 = max(c for _, c in block_cells)

    markers = [
        (r, c, grid[r][c])
        for r in range(rows)
        for c in range(cols)
        if grid[r][c] not in (background, block_color)
    ]

    out = [row[:] for row in grid]

    # Fill the horizontal and vertical arms of the cross.
    for r in range(r0, r1 + 1):
        for c in range(cols):
            out[r][c] = block_color
    for r in range(rows):
        for c in range(c0, c1 + 1):
            out[r][c] = block_color

    # A marker aligned with one arm preserves that lane as background on its side.
    for mr, mc, _ in markers:
        if mr < r0 and c0 <= mc <= c1:
            for r in range(0, r0):
                out[r][mc] = background
        elif mr > r1 and c0 <= mc <= c1:
            for r in range(r1 + 1, rows):
                out[r][mc] = background
        elif mc < c0 and r0 <= mr <= r1:
            for c in range(0, c0):
                out[mr][c] = background
        elif mc > c1 and r0 <= mr <= r1:
            for c in range(c1 + 1, cols):
                out[mr][c] = background

    # Markers survive the transformation.
    for r, c, color in markers:
        out[r][c] = color

    return out
