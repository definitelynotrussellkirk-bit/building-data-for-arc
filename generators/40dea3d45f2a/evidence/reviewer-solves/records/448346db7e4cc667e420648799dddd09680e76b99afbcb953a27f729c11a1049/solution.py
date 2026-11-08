"""Infer a shape-equivalence matrix from spatially ordered objects."""


def components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    objects = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in remaining:
                    remaining.remove(p)
                    cells.add(p)
                    todo.append(p)
        objects.append(cells)
    # Objects in one visual row may have different topmost occupied pixels.
    pending = sorted(objects, key=lambda cells: min(r for r, _ in cells))
    ordered = []
    while pending:
        band = [pending.pop(0)]
        bottom = max(r for r, _ in band[0])
        while pending and min(r for r, _ in pending[0]) <= bottom:
            band.append(pending.pop(0))
            bottom = max(bottom, max(r for r, _ in band[-1]))
        ordered.extend(sorted(band, key=lambda cells: min(c for _, c in cells)))
    return ordered


def shape_key(cells, reflections=True):
    variants = []
    for flip in ((1, -1) if reflections else (1,)):
        points = [(r, flip * c) for r, c in cells]
        for _ in range(4):
            r0 = min(r for r, _ in points)
            c0 = min(c for _, c in points)
            variants.append(tuple(sorted((r - r0, c - c0) for r, c in points)))
            points = [(c, -r) for r, c in points]
    return min(variants)


def solve(grid):
    keys = [shape_key(cells) for cells in components(grid)]
    return [[8 if a == b else 0 for b in keys] for a in keys]
