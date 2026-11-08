from collections import deque


def _nonzero_components(grid):
    """Return 4-connected monochrome nonzero components."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    components = []

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue

            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
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
                        q.append((nr, nc))

            components.append((color, cells))

    return components


def solve(grid):
    """
    Read each left-to-right colored frame as an encoded tile.

    The payload is the frame's interior with foreground/background inverted:
    an interior foreground cell becomes 0 and an interior 0 becomes the
    frame color.  Payloads are top-aligned and separated by one zero column.
    """
    pieces = []
    for color, cells in _nonzero_components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)

        # The visible tasks use proper frames with a non-empty interior.
        interior = [
            [0 if grid[r][c] == color else color for c in range(c0 + 1, c1)]
            for r in range(r0 + 1, r1)
        ]
        pieces.append((c0, interior))

    pieces.sort(key=lambda item: item[0])
    if not pieces:
        return []

    height = max(len(piece) for _, piece in pieces)
    widths = [len(piece[0]) if piece else 0 for _, piece in pieces]
    out_width = sum(widths) + max(0, len(pieces) - 1)
    out = [[0 for _ in range(out_width)] for _ in range(height)]

    offset = 0
    for index, (_, piece) in enumerate(pieces):
        width = widths[index]
        for r, row in enumerate(piece):
            out[r][offset : offset + width] = row
        offset += width
        if index + 1 < len(pieces):
            offset += 1

    return out
