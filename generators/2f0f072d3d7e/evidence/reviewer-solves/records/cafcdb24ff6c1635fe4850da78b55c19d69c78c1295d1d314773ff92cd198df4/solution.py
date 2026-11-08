"""Infer a shape analogy from two example panels; recolor chosen panel to 8."""

def _normal(points):
    if not points:
        return frozenset()
    r0, c0 = min(r for r,c in points), min(c for r,c in points)
    return frozenset((r-r0,c-c0) for r,c in points)


def _transform(points, name):
    f = {
        'cw': lambda r,c: (c,-r),
        'ccw': lambda r,c: (-c,r),
        'half': lambda r,c: (-r,-c),
        'lr': lambda r,c: (r,-c),
        'ud': lambda r,c: (-r,c),
        'transpose': lambda r,c: (c,r),
        'antitranspose': lambda r,c: (-c,-r),
        'identity': lambda r,c: (r,c),
    }[name]
    return _normal([f(r,c) for r,c in points])


def solve(grid):
    if not grid or not grid[0]:
        raise ValueError('Empty grid')
    h,w = len(grid),len(grid[0])
    cuts = [c for c in range(w) if all(row[c] == 9 for row in grid)]
    bounds = [-1] + cuts + [w]
    panels = [[row[a+1:b] for row in grid] for a,b in zip(bounds,bounds[1:]) if b>a+1]
    if len(panels) != 6:
        raise ValueError('Expected six panels separated by color 9')
    shapes = [_normal([(r,c) for r,row in enumerate(p) for c,v in enumerate(row) if v != 0]) for p in panels]
    matches = []
    for name in ('cw','ccw','half','lr','ud','transpose','antitranspose','identity'):
        if _transform(shapes[0],name) == shapes[1]:
            wanted = _transform(shapes[2],name)
            matches.extend((name,i) for i in range(3,6) if shapes[i] == wanted)
    if not matches:
        raise ValueError('No candidate fits the panel analogy')
    # Symmetric anchors can leave several candidates consistent. A fixed order
    # makes the prediction reproducible; it does not resolve the ambiguity.
    chosen = panels[matches[0][1]]
    return [[8 if v else 0 for v in row] for row in chosen]
