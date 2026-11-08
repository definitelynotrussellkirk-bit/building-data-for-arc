from itertools import combinations


def _primitives(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    squares = []
    for r in range(h - 1):
        for c in range(w - 1):
            shape = frozenset({(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)})
            if shape <= cells:
                squares.append(("square", shape, (r, c)))

    lines = []
    for r in range(h):
        for start in range(w):
            for end in range(start + 2, w):
                shape = frozenset((r, c) for c in range(start, end + 1))
                if shape <= cells:
                    lines.append(("line", shape, (0, r, start, end)))
                else:
                    break
    for c in range(w):
        for start in range(h):
            for end in range(start + 2, h):
                shape = frozenset((r, c) for r in range(start, end + 1))
                if shape <= cells:
                    lines.append(("line", shape, (1, c, start, end)))
                else:
                    break
    return cells, squares + lines


def _best_cover(cells, primitives):
    # The examples look like unions of 2x2 blocks and straight bars.  Prefer the
    # smallest number of objects, then the least overlap/shortest total drawing.
    for count in range(1, min(8, len(primitives)) + 1):
        candidates = []
        for chosen in combinations(range(len(primitives)), count):
            union = set()
            for index in chosen:
                union.update(primitives[index][1])
            if union == cells:
                total_area = sum(len(primitives[index][1]) for index in chosen)
                key = (
                    total_area,
                    tuple(primitives[index][2] for index in chosen),
                )
                candidates.append((key, chosen))
        if candidates:
            return min(candidates)[1]
    return ()


def solve(grid):
    cells, primitives = _primitives(grid)
    chosen = _best_cover(cells, primitives)
    line_cells = set()
    for index in chosen:
        if primitives[index][0] == "line":
            line_cells.update(primitives[index][1])

    return [
        [0 if value == 0 else (2 if (r, c) in line_cells else 8) for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]
