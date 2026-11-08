"""Visible-example solution for the post-repair episode."""


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (1 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _cw(g):
    return [list(row) for row in zip(*g[::-1])]


def _rot180(g):
    return [row[::-1] for row in g[::-1]]


def _ccw(g):
    return [list(row) for row in zip(*g)][::-1]


def solve(grid):
    commands = [v for v in grid[0] if v in (2, 3, 4, 5)]
    objects = _components(grid)
    selected = sorted(
        objects,
        key=lambda cells: (-len(cells), _bbox(cells)[0], _bbox(cells)[1]),
    )[0]
    r1, c1, r2, c2 = _bbox(selected)
    template = [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]

    copies = []
    for command in commands:
        if command == 2:
            piece = [row[:] for row in template]
        elif command == 3:
            piece = _cw(template)
        elif command == 4:
            piece = _rot180(template)
        else:
            piece = _ccw(template)
        copies.append(piece)

    h = max(len(piece) for piece in copies)
    w = sum(len(piece[0]) for piece in copies) + len(copies) - 1
    out = [[0] * w for _ in range(h)]
    left = 0
    for piece in copies:
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    out[r][left + c] = value
        left += len(piece[0]) + 1
    return out
