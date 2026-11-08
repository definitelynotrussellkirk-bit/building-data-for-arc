from collections import deque


def solve(grid):
    h, w = len(grid), len(grid[0])

    # The non-background, non-object cells in column 0 form an ordered palette.
    palette = [grid[r][0] for r in range(h) if grid[r][0] not in (0, 3)]

    # Extract 4-connected color-3 components.
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or (r, c) in seen:
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
                        and grid[nr][nc] == 3
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)

    def bounds(cells):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return min(rows), min(cols), max(rows), max(cols)

    # Visible examples show descending cell count; position resolves any tie.
    components.sort(key=lambda cells: (-len(cells), bounds(cells)[0], bounds(cells)[1]))

    pieces = []
    for cells, color in zip(components, palette):
        r0, c0, r1, c1 = bounds(cells)
        piece = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
        for r, c in cells:
            piece[r - r0][c - c0] = color
        pieces.append(piece)

    if not pieces:
        return [[0]]
    out_w = max(len(piece[0]) for piece in pieces)
    out_h = sum(len(piece) for piece in pieces) + len(pieces) - 1
    output = [[0] * out_w for _ in range(out_h)]
    top = 0
    for piece in pieces:
        for r, row in enumerate(piece):
            output[top + r][: len(row)] = row
        top += len(piece) + 1
    return output
